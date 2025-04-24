pipeline {
    agent any

    environment {
        DOCKER_PASS = credentials('docker-hub-password')
        DOCKER_IMAGE = 'amarocket//maas_api_metrics_exporter'
        DOCKER_SERVICE = "maas_prometheus_metrics_adapter_service"
        DOCKER_USER = credentials('docker-hub-username')
        LOG_FILE = "/var/log/docker_auto_update.log"
        MAAS_API_KEY = credentials('maas-api-key')
        MAAS_API_URL = credentials('maas_api_ip')
    }

    stages {
        stage('Clone Repository') {
            steps {
                dir('/var/lib/jenkins/workspace/MAAS_Metrics_API_Exporter/') {
                    script {
                        if (fileExists('.git')) {
                            sh 'git stash || true'
                            sh 'git pull origin main'
                        } else {
                            git branch: 'main', url: 'https://github.com/AmaRocket/MAAS-Monitoring.git'
                        }
                    }
                }
            }
        }

        stage('Build and Push Docker Image') {
            steps {
                dir('/var/lib/jenkins/workspace/MAAS_Metrics_API_Exporter//') {
                    script {
                        sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker build --no-cache -t $DOCKER_IMAGE:latest .
                        docker push $DOCKER_IMAGE:latest
                        echo $DOCKER_IMAGE was deployed.
                        '''
                    }
                }
            }
        }


        stage('Remove Docker Swarm Service') {
            steps {
                script {
                    sh '''
                        echo "Updating Docker Swarm service..." | tee -a $LOG_FILE
                        echo "Removing the existing Docker Swarm service..." | tee -a $LOG_FILE
                        docker service rm $DOCKER_SERVICE || true
                        sleep 5
                        echo "Waiting for the port to be free..."
                        while netstat -tuln | grep -q ":9200 "; do
                            echo "Port 9200 still in use, waiting..."
                            sleep 2
                        done
                        echo "Port 9200 is now free, continuing..." | tee -a $LOG_FILE
                        '''
                }
            }
        }

        stage('Start Docker Swarm Service') {
            steps {
                script {
                    sh '''
                        echo "Re-creating Docker Swarm service..." | tee -a $LOG_FILE
                        docker service create \
                            --name $DOCKER_SERVICE \
                            --constraint 'node.labels.role == manager' \
                            --network host \
                            -e MAAS_API_KEY=$MAAS_API_KEY \
                            -e MAAS_API_URL=$MAAS_API_URL \
                            --restart-condition on-failure \
                            --replicas 1 \
                            $DOCKER_IMAGE:latest
                        echo "Docker Swarm service recreated successfully." | tee -a $LOG_FILE
                        '''
                }
            }
        }

    }

    post {
        success {
            echo '✅ Deployment successful!'
        }
        failure {
            echo '❌ Deployment failed.'
        }
    }
}