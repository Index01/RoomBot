import "bootstrap/dist/css/bootstrap.css";
import "../styles/modals.css";
import { Col, Row, Table } from "react-bootstrap";
import {
  DatatableWrapper,
  TableBody,
  TableColumnType,
  TableHeader
} from "react-bs-datatable";
import { WaittimeEdit, WaittimeDelete } from "./waittimes_edit.js";
import axios from 'axios';
import Button from 'react-bootstrap/Button';
import React from "react";
import Modal from 'react-bootstrap/Modal';
import Form from 'react-bootstrap/Form';
import toast, { Toaster } from 'react-hot-toast';
import { useParams } from "react-router-dom";
import { Display } from "react-7-segment-display";

function withParams(Component) {
  return props => <Component {...props} params={useParams()} />;
}

class aaaHowLongTho extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      short_name: this.props.params.slug,
      name: '',
      seconds: '',
      minutes: '',
      hours: '',
      lenght: 0
    }
    this.wait_url = window.location.protocol + "//" + window.location.hostname + ":8000/api/wait/" + this.state.short_name + "/";
  }
  componentDidMount() {
    axios.get(this.wait_url)
      .then((result) => {
	var hours = Math.floor(result.data.time / 3600);
	var minutes = Math.floor((result.data.time - (hours * 3600)) / 60);
	var seconds = result.data.time - (hours * 3600) - (minutes * 60);
	this.setState({name: result.data.name,
		       hours: hours,
		       minutes: minutes,
		       seconds: seconds,
		       skew: true});
      });
  }
  render() {
    return(
      <>
	<Row>
	  <Col>
	    <a href="/waittime">Wait Time</a> for {this.state.name}
	  </Col>
	</Row>
	<Row>
	  <Col lg={3}>Hours</Col>
	  <Col lg={3}>Minutes</Col>
	  <Col lg={3}>Seconds</Col>
	</Row>
	<Row>
	  <Col lg={3}>
	    <Display value={this.state.hours ? this.state.hours : '00'} skew="true" />
	  </Col>
	  <Col lg={3}>
	    <Display value={this.state.minutes ? this.state.minutes : '00'} skew="true" />
	  </Col>
	  <Col lg={3}>
	    <Display value={this.state.seconds ? this.state.seconds : '00'} skew="true" />
	  </Col>
	</Row>
      </>
    )
  }
};
export const HowLongTho = withParams(aaaHowLongTho);

export class TheTimers extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      waittimes: []
    };
    this.loadWaits = this.loadWaits.bind(this);
  }

  loadWaits() {
    console.log("Whuuuut");
    axios.get(window.location.protocol + "//" + window.location.hostname + ":8000/api/wait/")
      .then((result) => {
	console.log("Lolooll " + JSON.stringify(result.data));
	this.setState({waittimes: result.data});
      })
  }

  componentDidMount() {
    this.loadWaits()
  }

  waitHeaderFactory() {
    let WAIT_HEADERS: TableColumnType<ArrayElementType>[] = [
      {
	prop: "name",
	cell: (row) => ( <a href={"/waittime/" + row.short_name}>{row.name}</a> ),
	title: "Name"
      },
      {
	prop: "button",
	cell: (row) => ( <WaittimeEdit short_name={row.short_name} reload={this.loadWaits}/> )
      },
      {
	prop: "button",
	cell: (row) => ( <WaittimeDelete key={Math.random()} short_name={row.short_name} reload={this.loadWaits}/> )
      }

    ];
    return WAIT_HEADERS;
  }
  render(){
    return(
      <>
      <div>
	<WaittimeEdit key={Math.random()} reload={this.loadWaits}/>
      </div>
      <div>
	<DatatableWrapper body={this.state.waittimes} headers={this.waitHeaderFactory()}>
	  <Row className="mb-4 p-2">
	    <Col xs={12} lg={4} className="d-flex flex-col justify-content-end align-items-end" />
	    <Col xs={2} mb={1} lg={1} className="d-flex flex-col justify-content-lg-center align-items-center justify-content-sm-start mb-2 mb-sm-0"/>
	    <Col xs={2} mb={1} lg={1} className="d-flex flex-col justify-content-lg-center align-items-center justify-content-sm-start mb-2 mb-sm-0"/>
	  </Row>
	  <Table>
	    <TableHeader />
	    <TableBody />
	  </Table>
	</DatatableWrapper>
      </div>
      </>
    );
  }
}
