import os, json, base64, time, decimal
import boto3

runtime = boto3.client("sagemaker-runtime")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["DDB_TABLE"])

SM_ENDPOINT = os.environ["SM_ENDPOINT_NAME"]
THRESHOLD = float(os.environ.get("THRESHOLD", "0.5"))

def to_csv_ordered(sensor):
    # Keep feature order EXACTLY as the training CSV (no label at inference):
    # temp_c,humidity_pct,vibration_g,pressure_kpa,voltage_v,current_a
    fields = [
        sensor.get("temp_c", 0.0),
        sensor.get("humidity_pct", 0.0),
        sensor.get("vibration_g", 0.0),
        sensor.get("pressure_kpa", 0.0),
        sensor.get("voltage_v", 0.0),
        sensor.get("current_a", 0.0),
    ]
    # Build a single CSV line (no header, no label)
    return ",".join(str(x) for x in fields)

def infer_one(csv_line):
    resp = runtime.invoke_endpoint(
        EndpointName=SM_ENDPOINT,
        ContentType="text/csv",   # XGBoost expects CSV input
        Accept="text/csv",
        Body=csv_line.encode("utf-8"),
    )
    body = resp["Body"].read().decode("utf-8").strip()
    # XGBoost returns one score per line (CSV). Parse float.
    return float(body.split(",")[0])

def put_ddb(item):
    # Convert floats safely for DynamoDB
    def _num(x):
        return decimal.Decimal(str(x))
    table.put_item(Item={
        "pk": f'{item["deviceId"]}#{time.strftime("%Y-%m-%d", time.gmtime(item["ts"]/1000))}',
        "ts": int(item["ts"]),
        "deviceId": item["deviceId"],
        "temp_c": _num(item["temp_c"]),
        "humidity_pct": _num(item["humidity_pct"]),
        "vibration_g": _num(item["vibration_g"]),
        "pressure_kpa": _num(item["pressure_kpa"]),
        "voltage_v": _num(item["voltage_v"]),
        "current_a": _num(item["current_a"]),
        "score": _num(item["score"]),
        "anomaly": int(item["anomaly"]),
    })

def handler(event, context):
    for rec in event.get("Records", []):
        payload = rec["kinesis"]["data"]
        data = json.loads(base64.b64decode(payload))
        # Expected JSON from producer:
        # { "deviceId": "...", "ts": 1690000000000, "temp_c":..., "humidity_pct":..., "vibration_g":..., "pressure_kpa":..., "voltage_v":..., "current_a":... }
        csv_line = to_csv_ordered(data)
        score = infer_one(csv_line)
        anomaly = 1 if score >= THRESHOLD else 0

        put_ddb({
            **data,
            "score": score,
            "anomaly": anomaly,
        })
    return {"ok": True}
