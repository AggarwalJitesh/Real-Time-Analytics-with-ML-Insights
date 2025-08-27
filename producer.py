import json, time, random, uuid
import boto3

REGION = "ap-south-1"
STREAM = "iot-sensor-stream"
kinesis = boto3.client("kinesis", region_name=REGION)

def sample_point(device_id):
    # Generate mostly-normal readings + occasional spikes (anomalies)
    base = {
        "temp_c": random.normalvariate(28, 3),
        "humidity_pct": max(0, min(100, random.normalvariate(40, 7))),
        "vibration_g": abs(random.normalvariate(0.03, 0.02)),
        "pressure_kpa": random.normalvariate(101, 2),
        "voltage_v": random.normalvariate(12.0, 0.2),
        "current_a": abs(random.normalvariate(0.8, 0.1)),
    }
    # 2% chance of a bad spike
    if random.random() < 0.02:
        base.update({
            "temp_c": random.uniform(70, 90),
            "vibration_g": random.uniform(1.0, 2.0),
            "pressure_kpa": random.uniform(200, 260),
            "voltage_v": random.uniform(4, 6),
            "current_a": random.uniform(1.5, 3.0),
        })
    return {
        "deviceId": device_id,
        "ts": int(time.time() * 1000),
        **base
    }

def send_n(n=1000, devices=3):
    ids = [f"dev-{i+1}" for i in range(devices)]
    for _ in range(n):
        d = random.choice(ids)
        record = sample_point(d)
        kinesis.put_record(
            StreamName=STREAM,
            Data=json.dumps(record).encode("utf-8"),
            PartitionKey=record["deviceId"],
        )
        time.sleep(0.1)  # ~10 rps

if __name__ == "__main__":
    send_n(n=300)
