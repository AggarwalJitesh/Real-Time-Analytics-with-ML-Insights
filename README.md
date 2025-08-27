# Real-Time-Analytics-with-ML-Insights
Stream live IoT-like data, run ML inference in real-time, and visualize results in a live dashboard

Architecture Flow
#### IoT Data Simulator (Python)  →  Amazon Kinesis (Data Stream)  →  AWS Lambda (Consumer + Preprocessing)   →  Amazon SageMaker Endpoint (XGBoost Model Inference)  →  Amazon DynamoDB / S3 (Prediction Storage)  →  Amazon QuickSight (Real-Time Dashboard)  →  Amazon CloudWatch (Monitoring & Logs)


## Tech Stack

* **Amazon Kinesis** → Ingests real-time streaming data.
* **AWS Lambda** → Consumes events from Kinesis and invokes ML inference.
* **Amazon SageMaker** → Hosts a deployed **XGBoost** model for predictions.
* **Amazon DynamoDB / S3** → Stores inference results with timestamps.
* **Amazon QuickSight** → Visualizes stored data in live dashboards.
* **Amazon CloudWatch** → Monitors Lambda errors, Kinesis throughput, and system health.
* **Python (boto3)** → Data simulator that pushes IoT data into Kinesis.

---

## 0) Prereqs (one-time)
**IAM roles:**

   * A **Lambda execution role** with permissions for kinesis:*, dynamodb:PutItem, s3:PutObject, sagemaker:InvokeEndpoint, logs:*
   * A **SageMaker execution role** with access to read training data in S3 and write model artifacts to S3.

<img width="1439" height="773" alt="3" src="https://github.com/user-attachments/assets/21f13db0-63fe-42b5-b2b3-9bc7f938ae66" />
<img width="1439" height="773" alt="4" src="https://github.com/user-attachments/assets/c84d1a95-b347-46e8-bcdb-0b76ebdbe925" />


### 1. **Data Simulation**

* Write a Python script (producer.py) that generates synthetic IoT data
* Use boto3 SDK to push JSON events into **Amazon Kinesis**
* Ran locally on Mac

<img width="1439" height="773" alt="1" src="https://github.com/user-attachments/assets/d3282aba-5dba-46e5-8dd8-6ce8e5d0e17d" />



### 2. **Kinesis Setup**

* In AWS Console → Kinesis → Create a Data Stream
* Name: iot-sensor-stream
* Capacity mode: **On-demand** 
<img width="1439" height="773" alt="2" src="https://github.com/user-attachments/assets/072ee474-3852-4277-b533-c83e33b6576d" />



### 3. **Model Training / Deployment**

## Prepare a tiny XGBoost training dataset 

**Columns (in order):**
label,temp_c,humidity_pct,vibration_g,pressure_kpa,voltage_v,current_a

* Go to **S3 → your bucket → Upload** iot_train.csv
<img width="1439" height="773" alt="5" src="https://github.com/user-attachments/assets/bef323de-759d-470f-a06b-9ac49480f0c3" />

## Train a tiny XGBoost model in SageMaker 

Go to **SageMaker → Training → Training jobs → Create training job**.
**Job settings**: name xgb-iot-anomaly-train
**Algorithm source**: **Built-in algorithm** → **XGBoost** 
**Hyperparameters**

   * objective= binary:logistic
   * num_round=100
   * max_depth=5
   * eta=0.2
   * subsample=0.8
   * eval_metric=auc
**Create training job** and wait until **Completed**.

<img width="1439" height="773" alt="6" src="https://github.com/user-attachments/assets/5b1020a1-bdde-4eba-9037-21359179a515" />
<img width="1439" height="773" alt="7" src="https://github.com/user-attachments/assets/783945a1-6031-43a3-ad4b-263b020273a7" />
<img width="1439" height="773" alt="8" src="https://github.com/user-attachments/assets/8f3f86f1-5f34-42cb-8ef9-a54525511cfd" />


## Deploy a real-time endpoint (Console)

From the **Completed training job** page:

1. Click **Create model** 
2. Then **Create endpoint configuration** 
3. Then **Create endpoint** 
4. Wait until status: **InService**.
<img width="1439" height="773" alt="9" src="https://github.com/user-attachments/assets/ea6fe95c-5649-4ba9-ae0c-d65c4854f5f6" />

<img width="1439" height="773" alt="10" src="https://github.com/user-attachments/assets/282d11d9-e9e4-4367-a6dc-1f264de35b47" />



### 4. **Lambda Function**

   * Name: kinesis-iot-infer
   * Runtime: **Python 3.12**
**Add environment variables**:

   * SM_ENDPOINT_NAME = xgb-iot-endpoint
   * THRESHOLD = 0.5  (classify > 0.5 as anomaly)
   * DDB_TABLE = iot_predictions
**Add Kinesis trigger**:

   * Triggers → **Add trigger** → **Kinesis** → choose iot-sensor-stream
   * Batch size: 100
   * Starting position: **LATEST**

<img width="1439" height="773" alt="12" src="https://github.com/user-attachments/assets/c4b0a9c7-6d46-46ef-88b7-0ffb650b5ad5" />
<img width="1439" height="773" alt="13" src="https://github.com/user-attachments/assets/5c20e486-d8dc-47c0-98b9-f4cf74f16bc8" />
<img width="1439" height="773" alt="14" src="https://github.com/user-attachments/assets/feb4c63c-f237-44d5-804b-8357942be09f" />
<img width="1439" height="773" alt="15" src="https://github.com/user-attachments/assets/7ff0450b-edb9-4f63-9768-5e01f2e44e49" />


### 5. **Data Storage**
* **DynamoDB → Create table**

  * Name: iot_predictions
  * Partition key: pk (String) → pattern: ${deviceId}#${yyyy-mm-dd}
  * Sort key: ts (Number) → epoch millis
<img width="1439" height="773" alt="11" src="https://github.com/user-attachments/assets/ed624ac1-26ad-4828-bccf-e543064ca988" />

### 6. **Visualization with QuickSight**

* Connect QuickSight to DynamoDB/S3 dataset.
* Create real-time dashboard (line chart for time-series, scatter for anomalies, etc.).

### 7. **Monitoring**

* Use **CloudWatch** to:

  * Monitor Kinesis stream throughput.
  * Track Lambda execution failures/errors.
  * Set alarms for anomalies.

---

## ⚡ Local Setup (Mac/Linux Example)

1. **Clone repo & create venv**

   bash
   python3 -m venv venv
   source venv/bin/activate
   pip install boto3
   

2. **Configure AWS CLI**

   bash
   aws configure
   

   Provide:

   * AWS Access Key ID
   * AWS Secret Access Key
   * Region (e.g., ap-south-1)

3. **Run producer**

   bash
   python producer.py
   

---

---


