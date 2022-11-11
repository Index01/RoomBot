import "../styles/Login.css";
import React from 'react';
import axios from 'axios';
import { useState } from 'react';


export default class LoginForm extends React.Component {
    constructor(props) {
       super(props);
   
       this.state = {
               errmrMessage: "",
               redirect: false
       };
   
       this.handleSubmit = this.handleSubmit.bind(this); 
   
       }


    handleSubmit() {  
        e.preventDefault();
        var { uname, pass } = document.forms[0];
        const email = uname.value;
        const otp = pass.value;
    
        axios.post(process.env.REACT_APP_BASE_URL+":8000/api/login/", {
                guest_email: email,
                jwt: otp
          })
          .then(res => {
	    throw new Error("Something went badly wrong!");
	    //const data = res.data
            //console.log(data);
            //console.log("rcvd resp");
            //window.localStorage.setItem('jwt', res.data);
            //localStorage.setItem('redirect', "true");
            //window.location.href = "http://ec2-3-21-92-196.us-east-2.compute.amazonaws.com:3000/rooms";
    
          })
          .catch((error) => {
	    throw new Error("Something went badly wrong!");
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
             //window.location = "/rooms";
             window.location.href = "http://ec2-3-21-92-196.us-east-2.compute.amazonaws.com:3000/rooms";
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


