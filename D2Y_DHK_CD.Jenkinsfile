// Jenkinsfile for deployment

pipeline {
    agent {
		label 'build-docker'
    }

    parameters {
        booleanParam(name: 'EXECUTE_RELEASE_STAGE', defaultValue: false, description: 'Execute release stage False by default')
        booleanParam(name: 'RESET_DB', defaultValue: false, description: 'Reset databases during deployment False by default')
        choice(name: 'ANSIBLE_TARGET_ENV', choices: 'none\ntest\nart\nrelease\nperf\nacc\nas1_bob\nas2_krv\nas3_bas\nas4_uvid\nas7_gdw\nas8_rvp', description: 'VM environment to deploy to')
    }

    stages {

        stage('Init') {
            steps {
                checkout scm
                echo "sprint: " + env.SPRINT_NUMBER
                echo "build: " + env.BUILD_NUMBER
                echo "branch: " + env.BRANCH_NAME

                sh "git rev-parse --short HEAD > src/version"
                sh "echo $BRANCH_NAME >> src/version"
                sh "echo $SPRINT_NUMBER >> src/version"
                sh "echo $BUILD_NUMBER >> src/version"

                println(params)
            }
        }

        stage('Package stage') {
            steps {
                sh "./ci-scripts/package.sh"
            }
        }

        stage('Release stage') {
        	when {
        	    expression { return params.EXECUTE_RELEASE_STAGE }
        	}
            steps {
                sh "./ci-scripts/release_upload.sh"
            }
        }

        stage('Deploy to VM'){
            when {
                expression { return params.ANSIBLE_TARGET_ENV != 'none' }
            }
            steps {
                script {
                    if (params.RESET_DB) {
                        env.RESET_DB_CLAUSE = "-e resetdb=true"
                    } else {
                        env.RESET_DB_CLAUSE = ""
                    }
                    if (params.ANSIBLE_TARGET_ENV.startsWith("as")) {
                        env.INVENTORY_CLAUSE = "ictu_test_hosts --limit " + params.ANSIBLE_TARGET_ENV.split('_')[1]
                    } else {
                        env.INVENTORY_CLAUSE = "ictu_" + params.ANSIBLE_TARGET_ENV + "_hosts"
                    }
                }
            	lock(env.ANSIBLE_TARGET_ENV) {
                    sh "./ci-scripts/ansible-deploy.sh"
                }
            }
		}
    }
    post {

        always {
            sh "echo 'done'"
    	}

    }
}