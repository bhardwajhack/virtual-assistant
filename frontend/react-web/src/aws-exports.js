// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

/**
 * AWS Configuration
 * 
 * This module exports configuration settings for AWS services used by the application.
 * Values are populated during deployment from CloudFormation outputs.
 */

/**
 * AWS Amplify authentication configuration.
 * Contains Cognito User Pool and Identity Pool settings for user authentication.
 * 
 * @constant
 * @type {Object}
 * @property {string} Auth.Cognito.userPoolClientId - Cognito User Pool Client ID
 * @property {string} Auth.Cognito.userPoolId - Cognito User Pool ID
 * @property {string} Auth.Cognito.identityPoolId - Cognito Identity Pool ID
 * @property {string} Auth.Cognito.region - AWS region for Cognito services
 */
export const awsConfig = {
    Auth: {
        Cognito: {
            userPoolClientId: '236cq8eukd1ue7gj1k1jlb5e2u',
            userPoolId: 'ap-south-1_B6Axy9fFu',
            identityPoolId: 'ap-south-1:9cae03c3-7f68-4c6a-b204-10943b5c8d1b',
            region: 'ap-south-1'
        }

    }
}

/**
 * WebSocket API secret
 * 
 * @constant
 * @type {string}
 */
export const apiKey = "Your-own-long-secret-text-to-access-the-api"

/**
 * WebSocket endpoint URL
 * 
 * @constant
 * @type {string}
 */
//export const apiUrl = "wss://vba.example.acme/ws"
export const apiUrl = "ws://localhost:8000/ws"

/**
 * Avatar .glb model filename
 * 
 * @constant
 * @type {string}
 */
export const avatarFileName = "sophia.glb"

/**
 * Avatar jaw bone name
 * 
 * @constant
 * @type {string}
 */
export const avatarJawboneName = "rp_sophia_animated_003_idling_jaw"
