#!/bin/bash

sleep_time=20
sleep 70
echo "This is Datasource instance$1 from DPS$2"
# sleep 15
echo "updating the config file"

INSTANCE_NUMBER=$1
DPS_NUMBER=$2

INDBF_IP_VAR="KAFKA_i${2}_IP"
INDBF_IP=${!INDBF_IP_VAR}
SAMP_NUMBER=$(($FED_CONFIG_R * $FED_CONFIG_E * $SAMP_CONSTANT))
RAW_DATA_TOPIC_NAME="collected_cpu_topic_$2"

echo INDBF_IP: $INDBF_IP, KAFKAPORT: $KAFKAPORT
export INDBF_IP RAW_DATA_TOPIC_NAME SAMP_NUMBER INSTANCE_NUMBER DPS_NUMBER
echo "Number of samples: ${SAMP_NUMBER}"

envsubst < /app/confs/collect_produce_ds_template.py > /data_sources/collect_produce_normal.py
envsubst < /app/confs/collect_produce_anomaly_template.py > /data_sources/collect_produce_anomaly.py
cp /app/confs/stress_background.py /data_sources/stress_background.py

echo "starting Datasource $1 from DPS$2"
echo "Going to be connected to iNDBF: $INDBF_IP, topic name: $RAW_DATA_TOPIC_NAME"
cd /data_sources/

echo ">>>> [$(date)] Sending Normal data for training..."

# For now this delay is related to machine specs
echo "Waiting for endbf to be ready..."
echo "This might take some time..."
for i in $(seq $sleep_time -1 1); do
    if (( i % 10 == 0 )); then
        echo "$i seconds remaining..."
    fi
    sleep 1
done
python3 collect_produce_normal.py

if [ "$DPS_NUMBER" -eq 2 ]; then
    echo "***********************************************"
    echo ">>>> [$(date)] Starting alternating random/fixed  *****"
    echo "***********************************************"
    sleep 10

    for i in {1..3}; do

        echo "***********************************************"
        echo ">>>> [$(date)] Starting round ${i}..."
        echo "***********************************************"


        echo "***********************************************"
        echo ">>>> [$(date)] Sending ABNORMAL data for a Maximum of 3 minutes..."
        echo "***********************************************"
        timeout 180 python3 collect_produce_anomaly.py
        
        echo "[CLEANUP] Killing all remaining Python processes..."
        pkill -f python
    done
else
    echo ">>>> [$(date)] Continue ending Normal data ..."

    for i in {1..3}; do

        echo "***********************************************"
        echo ">>>> [$(date)] Starting round ${i}..."
        echo "***********************************************"
        python3 collect_produce_normal.py
        
    done
    
fi