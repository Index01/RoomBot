import LoginForm from '../components/login.js';
import "../styles/Login.css";
import React from 'react';

const LoginComponent = () => {
    return(
        <span className="auth-wrapper">
            <div className="auth-inner">
              <LoginForm />
            </div>
        </span>
    );
};

export default LoginComponent;

