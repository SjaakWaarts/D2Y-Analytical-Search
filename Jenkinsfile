#!groovy
//Jenkinsfile (Declarative Pipeline)

boolean defaultExecuteSonarStage = false
boolean defaultExecuteSecurityStage = false

pipeline {
    agent any

    parameters {
        booleanParam(name: 'NIGHTLY_CLEANUP', defaultValue: false, description: 'removes all containers and images')
        booleanParam(name: 'EXECUTE_COMPONENT_TESTS', defaultValue: true, description: 'execute component tests against a docker container')
        booleanParam(name: 'EXECUTE_INTEGRATION_TESTS', defaultValue: true, description: 'execute integration tests against a docker container')
        booleanParam(name: 'EXECUTE_SYSTEM_TESTS', defaultValue: true, description: 'execute system tests against a docker container')
        choice(name: 'EXECUTE_UI_TESTS', choices: 'chrome\nie\nnone', description: 'whether to execute UI tests and which browser to use')
        booleanParam(name: 'EXECUTE_ACCESSIBILITY_TESTS', defaultValue: false, description: 'execute axe tests against a docker container')

        booleanParam(name: 'EXECUTE_SONAR_STAGE', defaultValue: defaultExecuteSonarStage, description: 'Execute the sonar analysis')
        booleanParam(name: 'EXECUTE_SECURITY_STAGE', defaultValue: defaultExecuteSecurityStage, description: 'Execute the Security stage')
    }

    stages {

        stage('Init') {
            steps {
                checkout scm
                sh "rm -rf ./art/testresults"
                sh "mkdir -p ./art/testresults"
                echo "branch: " + env.BRANCH_NAME
                echo "sprint: " + env.SPRINT_NUMBER
                echo "build: " + env.BUILD_NUMBER
                echo "oracle db: " + env.BASTION_POOL_HOST

                script { env.REST_API_BUILD_DOCKER_TAG = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim() }

                sh "echo $REST_API_BUILD_DOCKER_TAG"
                sh "git rev-parse --short HEAD > art/version"
                sh "echo $BRANCH_NAME >> art/version"
                // sh "echo $SPRINT_NUMBER >> art/version"
                sh "echo $BUILD_NUMBER >> art/version"
                println(params)

               // only execute this stage when the build is nightly (standard is False)
                script {
                    if (params.NIGHTLY_CLEANUP) {
                        sh "./docker/cleanup-nightly.sh"
                    }
                }
                // sh "./docker/run-jenkins.sh"
                // sh "docker ps -a"
                // sh "docker exec testsuite${env.REST_API_BUILD_DOCKER_TAG}-${env.BUILD_NUMBER} mkdir -p /usr/src/app/testresults"
            }
        }

        stage('COMPONENT TESTS') {
            when {
                expression { return params.EXECUTE_COMPONENT_TESTS }
            }
            steps {
                // sh "docker exec testsuite${env.REST_API_BUILD_DOCKER_TAG}-${env.BUILD_NUMBER} pytest /usr/src/app/component --verbose --junitxml=/usr/src/app/testresults/componenttests/pytestreport_componenttest.xml"
                // sh "docker exec testsuite${env.REST_API_BUILD_DOCKER_TAG}-${env.BUILD_NUMBER} python3 /usr/src/app/component/add_timestamp_to_component.py"
                // sh "docker cp testsuite${env.REST_API_BUILD_DOCKER_TAG}-${env.BUILD_NUMBER}:/usr/src/app/testresults/componenttests ./art/testresults/componenttests"
				sh "python3 -m pytest art/dhk_comp_test.py"
            }
        }

        stage('Build') {
            steps {
                sh 'python --version'
            }
        }
    }
}