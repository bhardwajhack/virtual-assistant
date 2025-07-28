// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

/**
 * Application Entry Point
 * 
 * This is the main entry point for the Virtual Banking Assistant frontend application.
 * It configures AWS Amplify authentication and renders the root App component.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { Amplify } from 'aws-amplify';

// Import required styles
import '@aws-amplify/ui-react/styles.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import './index.css';

// Import components and configuration
import App from './App';
import reportWebVitals from './reportWebVitals';
import { awsConfig } from './aws-exports';

// Configure AWS Amplify with authentication settings
Amplify.configure(awsConfig);

// Create root element and render application
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);

// Initialize performance monitoring
// Pass a function to log results (e.g., reportWebVitals(console.log))
// or send to an analytics endpoint: https://bit.ly/CRA-vitals
reportWebVitals();
