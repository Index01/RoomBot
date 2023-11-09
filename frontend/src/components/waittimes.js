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
      lenght: 0,
      time: 0,
      countdown: false,
      updated: 0,
      timer: null
    }
    this.wait_url = window.location.protocol + "//" + window.location.hostname + ":8000/api/wait/" + this.state.short_name + "/";
    this.updateTime = this.updateTime.bind(this);
  }
  updateTime() {
    var hours, minutes, seconds;
    var actual_time  = this.state.time;
    if ( this.state.countdown ) {
      var actual_time = this.state.time - (Math.floor(Date.now() / 1000) - this.state.updated);
      if (actual_time > 0) {
	setTimeout(() => this.updateTime(), 1000);
      } else {
	actual_time = 0;
      }
    }
    hours = Math.floor(actual_time / 3600);
    minutes = Math.floor((actual_time - (hours * 3600)) / 60);
    seconds = actual_time - (hours * 3600) - (minutes * 60);
    console.log("Updating time (" + this.state.time + ") " + hours + ":" + minutes + ":" + seconds);
    this.setState({
      hours: hours,
      minutes: minutes,
      seconds: seconds
    });
  }
  componentDidMount() {
    axios.get(this.wait_url)
      .then((result) => {
	this.setState({name: result.data.name,
		       time: result.data.time,
		       countdown: result.data.countdown,
		       updated: Math.floor(new Date(result.data.updated_at).getTime() / 1000)
		      }, () => this.updateTime());
      });
  }
  render() {
    return(
      <>
	<Container fluid>
	  <Row>
	    <Col>
	      <a href="/waittime">Wait Time</a> for {this.state.name}
	    </Col>
	  </Row>
	  <Row>
	    <Col className="col-4 display-4">Hours</Col>
	    <Col className="col-4 display-4">Minutes</Col>
	    <Col className="col-4 display-4">Seconds</Col>
	  </Row>
	  <Row>
	    <Col className="col-4 d-block d-md-none">
	      <Display value={this.state.hours ? this.state.hours : '00'} skew="true" height="100"/>
	    </Col>
	    <Col className="col-4 d-none d-md-block">
	      <Display value={this.state.hours ? this.state.hours : '00'} skew="true" height="200"/>
	    </Col>
	    <Col className="col-4 d-block d-md-none">
	      <Display value={this.state.minutes ? this.state.minutes : '00'} skew="true" height="100" />
	    </Col>
	    <Col className="col-4 d-none d-md-block">
	      <Display value={this.state.minutes ? this.state.minutes : '00'} skew="true" height="200"/>
	    </Col>
	    <Col className="col-4 d-block d-md-none">
	      <Display value={this.state.seconds ? this.state.seconds : '00'} skew="true"  height="100"/>
	    </Col>
	    <Col className="col-4 d-none d-md-block">
	      <Display value={this.state.seconds ? this.state.seconds : '00'} skew="true" height="200"/>
	    </Col>
	  </Row>
	</Container>
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
