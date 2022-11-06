import "../styles/Login.css";
import React from 'react';
import axios from 'axios';
import { useState } from 'react';



class SubmitForm extends React.Component {
    state = {
        email: '',
        pass: '',
    };

    handleSubmit = event => {
        event.preventDefault();
        const guest = {
            email: this.state.email,
            jwt: this.state.pass
        }
        //TODO(tb): HackHackHack fix it when not live.
        if(this.state.pass==""){
                console.log("empty pass");
            axios.post('http://ec2-3-21-92-196.us-east-2.compute.amazonaws.com:8000/api/login_reset/', { guest })
            .then(res=>{
                //window.localStorage.setItem('jwt', res.data);
                //console.log(res);
                console.log(res.data);
                window.location = "/login" 
        })
        }
        else{
            axios.post('http://ec2-3-21-92-196.us-east-2.compute.amazonaws.com:8000/api/login/', { guest })
            .then(res=>{
                window.localStorage.setItem('jwt', res.data);
                console.log(res);
                console.log(res.data);
                window.location = "/rooms" 
            })
        }
    }

    handleReset = event => {
        event.preventDefault();
        const guest = {
            email: this.state.email,
        }
        axios.post('http://ec2-3-21-92-196.us-east-2.compute.amazonaws.com:8000/api/login_reset/', { guest })
        .then(res=>{
            //window.localStorage.setItem('jwt', res.data);
            //console.log(res);
            console.log(res.data);
            window.location = "/login" 
        })
    }

    handleChange = event =>{
        this.setState({ email: event.target.value});
    }
    handlePass = event =>{
        this.setState({ pass: event.target.value});
    }
    render() {
        return (
        <span className="auth-wrapper">
            <div className="auth-inner">
                <h3>Sign In</h3>
                <form onSubmit = { this.handleSubmit }>
                <div className="boxez">
                    <label> Email:
                    <input className="form-control" required type = "text" name = "email" placeholder="Enter Email" onChange= {this.handleChange}/>
                    </label>
                </div>
                <div className="boxez">
                    <label> Password:
                    <input className="form-control" type = "password" name = "pass" placeholder="Enter Password" onChange= {this.handlePass}/>
                    </label>
                </div>

                <div>
                <p>
                </p>
                </div>

                <div className="d-grid">
                    <button type = "submit" className="btn btn-primary"> Submit </button>
                </div>
                <p>
                </p>
                <div className="d-grid">
                    <button type = "submit" className="btn btn-primary"> RequestReset </button>
                </div>
                </form>
            </div>
        </span>
        );
    }
}
export default SubmitForm;



//TODO(tb): prolly want to move back to this paradigm
//import LoginForm from '../components/login.js';
//import "../styles/Login.css";
//import React from 'react';
//
//const LoginComponent = () => {
//    return(
//        <span className="auth-wrapper">
//            <div className="auth-inner">
//              <LoginForm />
//            </div>
//        </span>
//    );
//};
//
//export default LoginComponent;

