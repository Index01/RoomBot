import "../styles/Login.css";
import React from 'react';
import axios from 'axios';
import { useState } from 'react';
import { useNavigate, Navigate } from "react-router-dom";

    


export default class LoginForm extends React.Component {
    constructor(props) {
       super(props);
   
       this.state = {
               errorMessage: "",
               redirect: false
       };
   
       this.handleSubmit = this.handleSubmit.bind(this); 
   
       }


    handleSubmit() {  

        var { uname, pass } = document.forms[0];
        const email = uname.value;
        const otp = pass.value;
    
        axios.post(`http://192.168.4.24:8000/api/login/`, {
                guest_email: email,
                jwt: otp
          })
          .then(res => {
            localStorage.setItem('jwt', res.data);
            localStorage.setItem('redirect', "true");
    
          })
          .catch((error) => {
            this.setState({errorMessage: error.message});
            if (error.response) {
              console.log(error.response);
              console.log("server responded");
            } else if (error.request) {
              console.log("network error");
            } else {
              console.log(error);
            }
          });
    }
    componentDidMount(){
        console.log('Comp mount');
        const redirect_local = JSON.parse(localStorage.getItem('redirect'));
        console.log(redirect_local);

           if (redirect_local) {
             console.log('Redirectingggg');
             localStorage.setItem('redirect', "false");
             window.location = "/rooms";
           }
    }



    //shouldComponentUpdate = () => false
    render(){
        return(
          <form onSubmit={this.handleSubmit}>
            <h3>Sign In</h3>
            <div className="mb-3">
              <label>Email address</label>
              <input
                type="email"
                className="form-control"
                placeholder="Enter email"
                name="uname"
              />
            </div>
            <div className="mb-3">
              <label>Password</label>
              <input
                type="password"
                className="form-control"
                placeholder="Enter password"
                name="pass"
                required
              />
            </div>
            <div className="mb-3">
              <div className="custom-control custom-checkbox">
                <input
                  type="checkbox"
                  className="custom-control-input"
                  id="customCheck1"
                />
                <label className="custom-control-label" htmlFor="customCheck1">
                      Remember me
                </label>
              </div>
            </div>
            <div className="d-grid">
              <button type="submit" className="btn btn-primary">
                Submit
              </button>
            </div>
            <p className="forgot-password text-right">
              Forgot <a href="#">password?</a>
            </p>
              { this.state.errorMessage &&
                <h3 className="error"> { this.state.errorMessage } </h3> }
          </form>
        )
    }
}


