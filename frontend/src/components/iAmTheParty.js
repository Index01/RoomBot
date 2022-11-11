import "../styles/iAmTheParty.css";
import React from 'react';
import axios from 'axios';
import { useState } from 'react';


export default class IAmAParty extends React.Component {
    constructor(props) {
       super(props);
   
       this.state = {
               errmrMessage: "",
               redirect: false
       };
   
       //this.handleSubmit = this.handleSubmit.bind(this); 
   
       }


    //handleSubmit() {  
    handleClick() {  
    handleSubmit = event => {
        event.preventDefault();

        window.location = "/rooms";
        console.log("handling it");
        const party = {
            email: email,
            room_number: room_number,
            description: description,
            end_time: end_time
        }

        var { email, room_number, description, end_time } = document.forms[0];
        console.log(email, room_number, description, end_time);
        party.email = email.value;
        party.room_number = room_number.value;
        party.description = description.value;
        party.end_time = end_time.value;
    
        axios.post(process.env.REACT_APP_BASE_URL+":8000/api/iama_party/", { party })
          .then(res => {
            console.log(res.data);
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
//    componentDidMount(){
//
//    }


    render(){


        return(
          <form onSubmit = { this.handleSubmit }>
            <h3>I AM THE PARTY</h3>
            <div className="mb-3">
              <label>Room number</label>
              <input
                type="room_number"
                className="form-control"
                placeholder="Enter the room number of this party"
                name="room_number"
              />
            </div>
            <div className="mb-3">
              <label>Email address</label>
              <input
                type="email"
                className="form-control"
                placeholder="Enter the email on record for this room"
                name="email"
              />
            </div>
            <div className="mb-3">
              <label>description</label>
              <input
                type="description"
                className="form-control"
                placeholder="Enter a three word description of your party"
                name="description"
                required
              />
            </div>
            <div className="d-grid">
              <button type="submit" className="btn btn-primary" onClick={() => this.handleClick()}>
                Submit
              </button>
            </div>
          </form>
        )
    }
}

