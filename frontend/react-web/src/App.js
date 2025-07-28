// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

/**
 * Main Application Component
 * 
 * This is the root component of the Virtual Banking Assistant application.
 * It handles user authentication through AWS Cognito and renders the main
 * content when authenticated.
 */

import { Authenticator } from '@aws-amplify/ui-react';
import Content from './Content'
import './App.css';

function App() {
    /**
     * Custom components for the Authenticator
     * Provides a branded header for the login screen
     */
    const components = {
        Header() {
            return (
                <div className='d-flex flex-column justify-content-center text-center'>
                    <p className='h1'>
                        Virtual Banking Assistant
                    </p>
                    <p className='h5 mb-5 text-secondary'>
                        Powered by Amazon Nova Sonic
                    </p>
                </div>
            );
        }
    }

    return (
        <div className='app'>
            <Authenticator
                loginMechanisms={['email']}  // Only allow email-based login
                components={components}      // Use custom components
                hideSignUp                   // Disable self-service sign up
            >
                {({ signOut, user }) => {
                    return <Content signOut={signOut} user={user} />
                }}
            </Authenticator>
        </div>
    );
}

export default App;
