# Technical & Scientific Methodology Documentation

This document outlines the theoretical models, mathematical formulations, algorithmic logic, and data engineering decisions implemented within the **AI-Powered E-Commerce Sales and Customer Insights Dashboard**.

---

## 1. Data Engineering & Preprocessing Pipeline

### 1.1 Ingestion & Schema Harmonization
Real-world e-commerce data often uses diverse naming conventions (e.g., `order_id` vs `InvoiceNo`, `price` vs `UnitPrice`). The ingestion module standardizes incoming schemas via regular expression normalization and alias dictionary mapping.

### 1.2 Identification of Returns & Cancellations
In standard transaction databases (such as the UCI Online Retail dataset), cancellations and refunds are identified through two primary signals:
1. An alphanumeric `InvoiceNo` starting with the prefix `C` or `c`.
2. A negative unit quantity (`Quantity < 0`).

The pipeline flags these records as `IsCancelled = True` and computes financial metrics as:
$$\text{LineTotal} = \text{Quantity} \times \text{UnitPrice}$$
$$\text{GrossRevenue} = \sum_{\text{Quantity} > 0} \text{LineTotal}$$
$$\text{RefundAmount} = \sum_{\text{Quantity} < 0} |\text{LineTotal}|$$
$$\text{NetRevenue} = \text{GrossRevenue} - \text{RefundAmount} = \sum \text{LineTotal}$$

### 1.3 Outlier and Zero-Price Handling
Records where `UnitPrice` \(\le 0\) typically correspond to administrative gifts, system test entries, or inventory corrections. Because these distort consumer demand elasticity, they are pruned during standard cleaning.

---

## 2. RFM Feature Extraction & Customer Segmentation

### 2.1 Mathematical Formulation of RFM Metrics
Given an analysis reference date \(T_{\text{ref}}\) (defined as \(\max(\text{InvoiceDate}) + 1\text{ day}\)):

1. **Recency (\(R\)):** Elapsed days since the customer's most recent qualifying purchase:
   $$R_i = \min_{t \in \mathcal{T}_i} \left( T_{\text{ref}} - t \right) \quad [\text{days}]$$
   where \(\mathcal{T}_i\) is the set of completed transaction dates for customer \(i\).

2. **Frequency (\(F\)):** Number of distinct completed order invoices:
   $$F_i = |\text{Unique Invoices}_i|$$

3. **Monetary Value (\(M\)):** Net cumulative financial spend across all qualifying orders:
   $$M_i = \sum_{j \in \text{Orders}_i} \text{NetRevenue}_{i,j}$$

### 2.2 Skew-Aware Normalization & Standardization
Financial distributions in retail adhere to power-law distributions with severe right-skewness. Feeding raw monetary values into distance-based algorithms biases cluster centroids toward extreme outliers.

To rectify this, we apply a log-plus-one transformation followed by z-score standardization:
$$x' = \ln(1 + x)$$
$$z = \frac{x' - \mu_{x'}}{\sigma_{x'}}$$
where \(\mu_{x'}\) is the mean and \(\sigma_{x'}\) is the standard deviation of the log-transformed feature.

### 2.3 KMeans Clustering Objective
Given \(K\) clusters and standardized feature vectors \(z_i \in \mathbb{R}^3\), KMeans minimizes the Within-Cluster Sum of Squares (Inertia):
$$J = \sum_{k=1}^K \sum_{i \in C_k} \| z_i - \mu_k \|^2$$
where \(\mu_k = \frac{1}{|C_k|} \sum_{i \in C_k} z_i\) represents the cluster centroid.

### 2.4 Silhouette Analysis for Hyperparameter Tuning
To determine the optimal cluster count \(K \in [2, 6]\), the silhouette coefficient \(s(i)\) is computed for each sample:
$$s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}$$
where:
- \(a(i)\) is the mean intra-cluster distance between sample \(i\) and all other points in the same cluster.
- \(b(i)\) is the mean nearest-cluster distance between sample \(i\) and points in the closest neighboring cluster.

The overall silhouette score is the sample mean \(\bar{s} = \frac{1}{N}\sum_{i=1}^N s(i)\), bounded within \([-1, +1]\).

### 2.5 Dynamic Cluster Labeling Heuristic
Rather than assigning static names arbitrarily, the cluster centroids are ranked on normalized \(R\), \(F\), and \(M\) dimensions:
- **Champions / High-Value:** \(\text{Rank}(M) \ge 0.8 \land \text{Rank}(F) \ge 0.7 \land \text{Rank}(R) \ge 0.6\)
- **Loyal Customers:** \(\text{Rank}(F) \ge 0.6 \land \text{Rank}(R) \ge 0.5\)
- **Recent / Promising:** \(\text{Rank}(R) \ge 0.6 \land \text{Rank}(F) \le 0.5\)
- **At-Risk Customers:** \(\text{Rank}(R) \le 0.4 \land (\text{Rank}(M) \ge 0.5 \lor \text{Rank}(F) \ge 0.5)\)
- **Lost / Hibernating:** \(\text{Rank}(R) \le 0.3 \land \text{Rank}(M) \le 0.4\)

---

## 3. Machine Learning Sales Forecasting

### 3.1 Strict Chronological Splitting (No Data Leakage)
In time-series analysis, random shuffling of train/test splits (\(K\)-fold CV) violates temporal causality and introduces future information into training. The series is strictly partitioned chronologically:
$$\mathcal{D}_{\text{train}} = \{y_1, y_2, \dots, y_{T - h}\}, \quad \mathcal{D}_{\text{test}} = \{y_{T - h + 1}, \dots, y_T\}$$
where \(h = \lfloor \text{test\_ratio} \times T \rfloor\).

### 3.2 Baseline Model: Rolling Naive Mean
To prove statistical utility, all candidate models are benchmarked against a naive rolling baseline:
$$\hat{y}_{t+h}^{\text{baseline}} = \frac{1}{W} \sum_{k=0}^{W-1} y_{t-k} \quad (W = 7)$$

### 3.3 Candidate Model: Holt-Winters Exponential Smoothing (ETS)
The Holt-Winters additive model decomposes the series into level (\(l_t\)), trend (\(b_t\)), and seasonal components (\(s_t\)):
$$l_t = \alpha (y_t - s_{t-m}) + (1 - \alpha)(l_{t-1} + \phi b_{t-1})$$
$$b_t = \beta (l_t - l_{t-1}) + (1 - \beta)\phi b_{t-1}$$
$$s_t = \gamma (y_t - l_{t-1} - \phi b_{t-1}) + (1 - \gamma)s_{t-m}$$
$$\hat{y}_{t+h} = l_t + \sum_{i=1}^h \phi^i b_t + s_{t+h - m(k+1)}$$
where \(\alpha, \beta, \gamma \in [0, 1]\) are smoothing parameters, \(\phi\) is a trend dampening factor, and \(m = 7\) represents weekly seasonality.

### 3.4 Evaluation Metrics
1. **Mean Absolute Error (MAE):**
   $$\text{MAE} = \frac{1}{n} \sum_{t=1}^n |y_t - \hat{y}_t|$$
2. **Root Mean Squared Error (RMSE):**
   $$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{t=1}^n (y_t - \hat{y}_t)^2}$$
3. **Mean Absolute Percentage Error (MAPE):**
   $$\text{MAPE} = \frac{100\%}{n} \sum_{t=1}^n \left| \frac{y_t - \hat{y}_t}{y_t + \epsilon} \right|$$

### 3.5 Prediction Intervals
Uncertainty bounds expand over the forecast horizon \(h\) proportional to residual variance:
$$\hat{\sigma}_h = \hat{\sigma}_{\text{res}} \cdot \left(0.8 + 0.05 \sqrt{h}\right)$$
$$\text{Interval}_{95\%} = \left[ \max(0, \hat{y}_{t+h} - 1.96 \hat{\sigma}_h), \; \hat{y}_{t+h} + 1.96 \hat{\sigma}_h \right]$$

---

## 4. Market Basket Analysis & Association Rules

### 4.1 Frequent Itemset Metrics
Let \(D\) denote the set of all transaction baskets, and \(A, B\) denote disjoint item sets.

1. **Support:** Joint probability of co-occurrence:
   $$\text{Support}(A \implies B) = P(A \cap B) = \frac{|\{T \in D : A \cup B \subseteq T\}|}{|D|}$$

2. **Confidence:** Conditional probability of buying \(B\) given \(A\):
   $$\text{Confidence}(A \implies B) = P(B \mid A) = \frac{\text{Support}(A \cup B)}{\text{Support}(A)}$$

3. **Lift:** Ratio of observed joint probability to expected probability under complete independence:
   $$\text{Lift}(A \implies B) = \frac{P(B \mid A)}{P(B)} = \frac{\text{Support}(A \cup B)}{\text{Support}(A) \times \text{Support}(B)}$$
   - \(\text{Lift} > 1\): Strong positive affinity.
   - \(\text{Lift} = 1\): Independent purchasing behavior.
   - \(\text{Lift} < 1\): Substitute goods (cannibalization).

---

## 5. Sales Anomaly Detection

### 5.1 Rolling Variance Envelope
Computes baseline from prior observations to prevent an outlier from masking itself:
$$\mu_{t, W} = \frac{1}{W}\sum_{k=1}^W y_{t-k}, \quad \sigma_{t, W} = \sqrt{\frac{1}{W-1}\sum_{k=1}^W (y_{t-k} - \mu_{t, W})^2}$$
$$\text{Score}_t = \frac{|y_t - \mu_{t, W}|}{\max(\sigma_{t, W}, \epsilon)}$$
Flagged as potential anomaly when \(\text{Score}_t \ge \theta\) (default \(\theta = 2.5\)).

### 5.2 Robust Z-Score via Median Absolute Deviation (MAD)
Because sample mean and standard deviation are non-robust to extreme outliers, MAD uses the median:
$$\text{Median} = \text{Med}(Y)$$
$$\text{MAD} = \text{Med}(|Y - \text{Median}|)$$
$$\text{Score}_t = \frac{|y_t - \text{Median}|}{1.4826 \times \text{MAD}}$$
where \(1.4826\) is the asymptotic consistency constant for normally distributed data.

### 5.3 Isolation Forest
An ensemble of \(n = 100\) isolation trees constructed by recursively partitioning multi-dimensional feature vectors \(x = [y_t, \text{DayOfWeek}_t, \Delta y_t]\). An anomaly score \(s(x, n)\) is defined as:
$$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
where \(h(x)\) is the path length to isolate point \(x\), and \(c(n)\) is the average path length of unsuccessful searches in a Binary Search Tree.

---

## 6. Privacy-Preserving Local AI Architecture

### 6.1 Strict Data Sanitization Layer
To uphold academic and industrial privacy standards:
1. No raw transactional rows or customer email/name identifiers are ever serialized into prompts.
2. The analytical engine computes scalar summary totals (e.g., total sales, top 5 SKUs, segment means).
3. The prompt is assembled locally and delivered via standard HTTP JSON POST to `http://127.0.0.1:11434/api/generate`.
4. If the daemon is unreachable or disabled, queries route deterministically to keyword-indexed calculation methods without calling any generative model.
