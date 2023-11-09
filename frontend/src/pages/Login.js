import "../styles/Login.css";
import React from 'react';
import axios from 'axios';
import { useState } from 'react';
import toast, { Toaster } from 'react-hot-toast';
const notifyReset = () => toast.success("New password sent, assuming a valid account is found.");
const notifyLoginError = (msg) => toast.error("Login error: " + msg);
const someError = (msg) => toast.error("Oh No: " + msg);

class SubmitForm extends React.Component {
    state = {
        email: '',
        pass: '',
        party: false
    };

    handleSubmit = event => {
        event.preventDefault();
        const guest = {
            email: this.state.email,
            jwt: this.state.pass
        }
        if(this.state.pass==""){
            notifyLoginError("password cannot be empty");
        }
        else{
            axios.post(window.location.protocol + "//" + window.location.hostname + ":8000/api/login/", guest )
            .then(res=>{
                window.localStorage.setItem('jwt', res.data);
                console.log(res);
                console.log(res.data);
                window.location = "/rooms"
            })
	    .catch((error) => {
	      if (error.response) {
		if (error.response.status == 401) {
		  notifyLoginError("invalid credentials");
		} else if (error.request) {
		  notifyLoginError("network error");
		} else if (error.request) {
		  notifyLoginError("unknown error");
		}
	      }
	    });
        }
    }

    handleReset = event => {
        event.preventDefault();
        const guest = {
            email: this.state.email,
        }
        console.log("Attempting reset request");
        axios.post(window.location.protocol + "//" + window.location.hostname + ":8000/api/login_reset/", { guest })
        .then(res=>{
          console.log(res.data);
          notifyReset();
        })
        .catch((error) => {
	  if (error.response) {
	    if (error.response.status) {
	      notifyLoginError("Unable to reset password");
	    } else if (error.request) {
	      notifyLoginError("network error");
	    } else if (error.request) {
	      notifyLoginError("unknown error");
	    }
	  }
	});
    }

    handleChange = event =>{
        this.setState({ email: event.target.value});
    }
    handlePass = event =>{
        this.setState({ pass: event.target.value});
    }
    componentDidMount() {
      axios.get(window.location.protocol + "//" + window.location.hostname + ":8000/api/login/")
	.then((res) => {
	  if (res.data.features.includes("party")) {
	    this.setState({party: true});
	  }
	})
        .catch((error) => {
	  if (error.response) {
	    someError("Mysterious error is mysterious.");
	  } else if (error.request) {
	    someError("Network error :(");
	  } else {
	    someError("Mysterious error is mysterious.");
	  }
	})
    }

    render() {
        var maybeLogin;
        if ( this.state.party ) {
	    maybeLogin = (
	      <div>
		<a href="/party_time">Find The Party</a>
	      </div>
	    )
        }
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
                    <button type="submit" className="btn btn-primary"> Submit </button>
                </div>
                <p>
                </p>
                <div className="d-grid">
                    <button type="submit" className="btn btn-primary" onClick={this.handleReset}> RequestReset </button>
                </div>
                </form>
	      <Toaster />
	      	  {maybeLogin}
            </div>
        </span>
        );
    }
}
export default SubmitForm;
