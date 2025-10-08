#!/bin/bash
sleep 15
echo "This is NDPPF_$1"

# echo "Waiting for brokers..."

EKAFKAIP_VAR="KAFKA_e${1}_IP"
EKAFKAIP=${!EKAFKAIP_VAR}

IKAFKAIP_VAR="KAFKA_i${1}_IP"
IKAFKAIP=${!IKAFKAIP_VAR}

TIMEOUT=5
#sleep 15

echo "You should see this message after kafka instances are up ..."
sleep 5

echo "starting NDPPF_$1 post processing container ..."

cp /app/confs/ndppf.py /network_data_preprocessing_function/

cd /network_data_preprocessing_function
echo "running: collected_cpu_topic_$1 preprocessed_cpu_topic_t_$1 preprocessed_cpu_topic_i_$1 ${IKAFKAIP}:${KAFKAPORT} ${EKAFKAIP}:${KAFKAPORT}"
python3 ndppf.py polling cpu 100 collected_cpu_topic_$1 preprocessed_cpu_topic_t_$1 preprocessed_cpu_topic_i_$1 ${IKAFKAIP}:${KAFKAPORT} ${EKAFKAIP}:${KAFKAPORT}
# sleep infinity