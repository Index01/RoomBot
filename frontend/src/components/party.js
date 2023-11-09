import "bootstrap/dist/css/bootstrap.css";
import "../styles/modals.css";
import Container from 'react-bootstrap/Container';
import { Col, Row, Table } from "react-bootstrap";
import {
  DatatableWrapper,
  TableBody,
  TableColumnType,
  TableHeader
} from "react-bs-datatable";
import axios from 'axios';
import Button from 'react-bootstrap/Button';
import React from "react";
import Modal from 'react-bootstrap/Modal';
import Form from 'react-bootstrap/Form';
import toast, { Toaster } from 'react-hot-toast';
import { useParams } from "react-router-dom";
const someError = (msg) => toast.error("Oh No: " + msg);
const itsOK = (msg) => toast.success(msg);

export class PartyTime extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      room_number: '',
      email: '',
      description: '',
      show: false
    }
    this.setEmail = this.setEmail.bind(this);
    this.setRoomNumber = this.setRoomNumber.bind(this);
    this.setDescription = this.setDescription.bind(this);
    this.newParty = this.newParty.bind(this);
    this.handleClose = this.handleClose.bind(this);
    this.handleOpen = this.handleOpen.bind(this);
  }
  handleClose() {
    this.setState({show: false});
  }
  handleOpen() {
    this.setState({show: true});
  }
  setEmail(event) {
    this.setState({email: event.target.value});
  }
  setRoomNumber(event) {
    this.setState({room_number: event.target.value});
  }
  setDescription(event) {
    this.setState({description: event.target.value});
  }
  newParty(event) {
    event.preventDefault();
    var data = {
      room_number: this.state.room_number,
      email: this.state.email,
      description: this.state.description
    }
    axios.post(window.location.protocol + "//" + window.location.hostname + ":8000/api/party/", data)
      .then(res => {
	this.props.reload();
	this.setState({show: false});
      })
      .catch((error) => {
	if (error.response) {
	  if (error.response.status == 400) {
	    someError("Unable to create party: " + error.response.data);
	  } else {
	    someError("Mysterious error is mysterious.");
	  }
	} else if (error.request) {
	  someError("Network error :(");
	} else {
	  someError("Mysterious error is mysterious.");
	}
      })
  }
  render() {
    return(
      <>
	<Button variant={"outline-primary"} size="sm" onClick={this.handleOpen}>
	  It Is Time To Party
	</Button>
	<Modal show={this.state.show} onHide={this.handleClose}>
	  <Modal.Header closeButton>
	    <Modal.Title>Where is the party at????</Modal.Title>
	  </Modal.Header>
	  <Modal.Body>
	    <Form onSubmit={this.newParty}>
	      <Form.Group className="mb-3" controlId="exampleForm.name">
		<Form.Label>Room Number</Form.Label>
		<Form.Control type="text" name="inputRoomNumber" value={this.state.room_number} onChange={this.setRoomNumber}/>
	      </Form.Group>
	      <Form.Group className="mb-3" controlId="exampleForm.name">
		<Form.Label>Associated Room Email</Form.Label>
		<Form.Control type="text" name="inputEmail" value={this.state.email} onChange={this.setEmail}/>
	      </Form.Group>
	      <Form.Group className="mb-3" controlId="exampleForm.name">
		<Form.Label>Room Description</Form.Label>
		<Form.Control type="text" name="inputDescription" value={this.state.description} onChange={this.setDescription}/>
	      </Form.Group>
	      <Button variant="primary" type="submit">
		Come on Barbie let's go Party
              </Button>
	    </Form>
	  </Modal.Body>
	</Modal>
      </>
    )
  }
}

export class PartyDelete extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      show: false,
      room_number: props.room_number,
      email: null
    }
    this.startDelete = this.startDelete.bind(this);
    this.plzDelete = this.plzDelete.bind(this);
    this.setEmail = this.setEmail.bind(this);
    this.handleClose = this.handleClose.bind(this);
  }
  handleClose() {
    this.setState({show: false});
  }
  setEmail(event) {
    this.setState({email: event.target.value});
  }
  startDelete() {
    this.setState({show: true});
  }
  plzDelete() {
    var data = {
      email: this.state.email
    }
    axios.delete(window.location.protocol + "//" + window.location.hostname + ":8000/api/party/" + this.state.room_number + "/", {data: data})
      .then(res => {
	itsOK("Deleted room");
	this.setState({show: false});
	this.props.reload();
      })
      .catch((error) => {
	if (error.response) {
	  if (error.response.status == 401) {
	    someError("Must specify actual room owners email. Do you know them?")
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
  render() {
    return(
      <>
	<Button variant={"outline-primary"} size="sm" onClick={this.startDelete}>
	  Delete
	</Button>
	<Modal show={this.state.show} onHide={this.handleClose}>
	  <Modal.Header closeButton>
	    <Modal.Title>Delete {this.state.name}???</Modal.Title>
	  </Modal.Header>
	  <Form.Group className="mb-3" controlId="exampleForm.email">
            <Form.Label>Room Email</Form.Label>
            <Form.Control type="text" name="inputName" onChange={this.setEmail}/>
	  </Form.Group>
	  <Modal.Body>
	    <Button variant={"danger"} size="sm" onClick={this.plzDelete}>
	      Really Delete?????
	    </Button>
	  </Modal.Body>
	</Modal>
      </>
    )
  }
}

export class TheParties extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      parties: []
    };
    this.loadParties = this.loadParties.bind(this);
  }

  loadParties() {
    axios.get(window.location.protocol + "//" + window.location.hostname + ":8000/api/party/")
      .then((result) => {
	this.setState({parties: result.data});
      })
      .catch((error) => {
	if (error.response) {
	  someError("Unable to load parties. You will have to adventure on your own.");
	} else if (error.request) {
	  someError("Network error :(");
	} else {
	  someError("Mysterious error is mysterious.");
	}
      })
  }

  componentDidMount() {
    this.loadParties()
  }
  partyHeaderFactory() {
    let PARTY_HEADERS: TableColumnType<ArrayElementType>[] = [
      {
	prop: "room_number",
	title: "Room Number"
      },
      {
         "prop": "description",
         "title": "Description"					},
      {
	prop: "button",
	cell: (row) => ( <PartyDelete key={Math.random()} room_number={row.room_number} reload={this.loadParties}/> )
      }

    ];
    return PARTY_HEADERS;
  }

  render() {
    return(
      <>
	<div>
	  <PartyTime key={Math.random()} reload={this.loadParties} />
	</div>
	<DatatableWrapper body={this.state.parties} headers={this.partyHeaderFactory()}>
	  <Row className="mb-4 p-2">
	    <Col lg={2} className="d-flex flex-col justify-content-end align-items-end" />
	    <Col lg={9} className="d-flex flex-col justify-content-end align-items-end" />
	    <Col lg={1} className="d-flex flex-col justify-content-lg-center align-items-center justify-content-sm-start mb-2 mb-sm-0"/>
	  </Row>
	  <Table>
	    <TableHeader />
	    <TableBody />
	  </Table>
	</DatatableWrapper>
      </>
    )
  }
}
