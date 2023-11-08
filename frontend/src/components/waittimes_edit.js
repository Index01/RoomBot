import "bootstrap/dist/css/bootstrap.css";
import "../styles/modals.css";
import axios from 'axios';
import Button from 'react-bootstrap/Button';
import React from "react";
import Modal from 'react-bootstrap/Modal';
import Form from 'react-bootstrap/Form';
import toast from 'react-hot-toast';
import { useState } from 'react';

const someError = (msg) => toast.error("Oh No: " + msg);
const itsOK = (msg) => toast.success(msg);

export class WaittimeDelete extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      short_name: this.props.short_name,
      has_password: false,
      password: '',
      show: this.props.show,
      name: ''
    }
    this.wait_url = window.location.protocol + "//" + window.location.hostname + ":8080/api/wait/" + this.state.short_name + "/";
    this.plzDelete = this.plzDelete.bind(this);
    this.startDelete = this.startDelete.bind(this);
    this.setPassword = this.setPassword.bind(this);
    this.handleClose = this.handleClose.bind(this);
  }
  setPassword(event) {
    this.setState({password: event.target.value});
  }
  startDelete(event) {
    this.setState({show: true});
    axios.get(this.wait_url)
      .then(res => {
	if (res.data.has_password) {
	  this.setState({has_password: true});
	}
	this.setState({name: res.data.name});
      })
      .catch((error) => {
	if (error.request) {
	  someError("Network error :(");
	} else {
	  someError("Mysterious error is mysterious.");
	}
      });

  }
  plzDelete(event) {
    var data = {};
    if (this.state.has_password) {
      data.password = this.state.password;
    }
    axios.delete(this.wait_url, {data: data})
      .then(res => {
	itsOK("Deleted wait time");
	this.setState({show: false});
	this.props.reload();
      })
      .catch((error) => {
	if (error.response) {
	  if (error.response.status == 401) {
	    someError("This wait time has a password. Do you know it?")
	  } else {
	    someError("Mysterious error is mysterious.");
	  }
	} else if (error.request) {
	  someError("Network error :(");
	} else {
	  someError("Mysterious error is mysterious.");
	}
      });

  }
  handleClose() {
    this.setState({show: false});
  }
  render() {
    let maybePassword;
    if ( this.state.has_password ) {
      maybePassword = (
	<>
	  <span>This waittime has a password. You must specify it.</span>
	  <Form.Group className="mb-3" controlId="exampleForm.ControlTextarea4">
            <Form.Label>Waittime Password</Form.Label>
            <Form.Control type="password" name="inputName" onChange={this.setPassword}/>
	  </Form.Group>
	</>
      )
    }

    return (
      <>
	<Button variant={"outline-primary"} size="sm" onClick={this.startDelete}>
	  Delete
	</Button>
	<Modal show={this.state.show} onHide={this.handleClose}>
	  <Modal.Header closeButton>
	    <Modal.Title>Delete {this.state.name}???</Modal.Title>
	  </Modal.Header>
	  <Modal.Body>
	    {maybePassword}
	    <Button variant={"danger"} size="sm" onClick={this.plzDelete}>
	      Really Delete?????
	    </Button>
	  </Modal.Body>
	</Modal>
      </>
    )
  }
}

export class WaittimeEdit extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      short_name: this.props.short_name ? this.props.short_name : '',
      name: '',
      time: '',
      new_password: '',
      show: this.props.show,
      is_new: true,
      has_password: false,
      password: true
    };
    this.wait_url = window.location.protocol + "//" + window.location.hostname + ":8080/api/wait/";
    this.startEdit = this.startEdit.bind(this);
    this.handleClose = this.handleClose.bind(this);
    this.setTime = this.setTime.bind(this);
    this.setNewPassword = this.setNewPassword.bind(this);
    this.setName = this.setName.bind(this);
    this.setShortName = this.setShortName.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.setPassword = this.setPassword.bind(this);
  }

  startEdit(event) {
    if (this.state.short_name) {
      this.state.is_new = false;
    }
    this.setState({show: true});
    if (! this.state.is_new) {
      axios.get(this.wait_url + this.state.short_name + "/")
	.then(res => {
	  this.setState({
	    name: res.data.name,
	    time: res.data.time
	  });
	  if (res.data.has_password) {
	    this.setState({has_password: true});
	  }
	})
        .catch((error) => {
	  if (error.request) {
	    someError("Network error :(");
	  } else {
	    someError("Mysterious error is mysterious.");
	  }
	});
    }
  }

  setTime(event) {
    this.setState({time: event.target.value});
  }

  setName(event) {
    this.setState({name: event.target.value});
  }

  setShortName(event) {
    this.setState({short_name: event.target.value});
  }

  setNewPassword(event) {
    this.setState({new_password: event.target.value});
  }

  setPassword(event) {
    this.setState({password: event.target.value});
  }

  handleClose() {
    this.setState({show: false});
  }
  handleSubmit(event) {
    event.preventDefault();
    let data;
    if (! this.state.is_new) {
      data = {
	time: this.state.time
      }
    } else {
      data = {
	time: this.state.time,
	name: this.state.name,
	short_name: this.state.short_name
      }
    }
    if ( this.state.new_password != '' ) {
      data.new_password = this.state.new_password;
    }
    if ( this.state.has_password ) {
      data.password = this.state.password;
    }
    if ( ! this.state.is_new ) {
      axios.put(this.wait_url + this.state.short_name + "/", data)
	.then(res => {
	  this.props.reload();
	  this.setState({show: false});
	})
      	.catch((error) => {
	  if (error.response) {
	    if (error.response.status == 400) {
	      someError("Unable to edit waittime!");
	    } else if (error.response.status == 401) {
	      someError("This wait time has a password. Do you know it?")
	    } else {
	      someError("Mysterious error is mysterious.");
	    }
	  } else if (error.request) {
	    someError("Network error :(");
	  } else {
	    someError("Mysterious error is mysterious.");
	  }
	});
    } else {
      axios.post(this.wait_url, data)
	.then(res => {
	  this.props.reload();
	  this.setState({show: false});
	})
	.catch((error) => {
	  if (error.response && error.response.status == 400) {
	    someError("Unable to create waittime!");
	  } else if (error.request) {
	    someError("Network error :(");
	  } else {
	    someError("Mysterious error is mysterious.");
	  }
	});
    }
  }
  render(){
    let maybeShortName;
    let maybePassword;
    if ( this.state.is_new ) {
      maybeShortName = (
	<Form.Group className="mb-3" controlId="exampleForm.ControlTextarea3">
          <Form.Label>The (short name) Is</Form.Label>
          <Form.Control type="text" name="inputShortName" value={this.state.short_name} onChange={this.setShortName}/>
	</Form.Group>
      );
    }
    if ( this.state.has_password ) {
      maybePassword = (
	<>
	<span>This waittime has a password. You must specify it.</span>
	<Form.Group className="mb-3" controlId="exampleForm.ControlTextarea4">
          <Form.Label>Waittime Password</Form.Label>
          <Form.Control type="password" name="inputName" onChange={this.setPassword}/>
	</Form.Group>
	</>
      )
    }
    return (
      <>
      <Button variant={"outline-primary"} size="sm" onClick={this.startEdit}>
      { this.state.short_name ? "Edit Waittime" : "New Waittime" }
      </Button>
      <Modal show={this.state.show} onHide={this.handleClose}>
        <Modal.Header closeButton>
          <Modal.Title>{ this.state.short_name ? "Edit Waittime: " + this.state.name : "New Waittime" }</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form onSubmit={this.handleSubmit}>
	    {maybeShortName}
	    {maybePassword}
	    <Form.Group className="mb-3" controlId="exampleForm.ControlTextarea4">
              <Form.Label>The Name Is</Form.Label>
              <Form.Control type="text" name="inputName" value={this.state.name} onChange={this.setName}/>
	    </Form.Group>
            <Form.Group className="mb-3" controlId="exampleForm.ControlTextarea1">
              <Form.Label>The Wait Time Is</Form.Label>
              <Form.Control type="text" name="inputWaitTime" value={this.state.time} onChange={this.setTime}/>
            </Form.Group>
            <Form.Group className="mb-3" controlId="exampleForm.ControlTextarea2">
              <Form.Label>New Password</Form.Label>
              <Form.Control type="password" name="inputPassword" onChange={this.setNewPassword} />
            </Form.Group>
            <Button variant="primary" type="submit">
              Submit
            </Button>
          </Form>
        </Modal.Body>
      </Modal>
      </>
    )
  }
}
