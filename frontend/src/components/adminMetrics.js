
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import axios from 'axios';
import React from "react";
import { Navigate } from "react-router-dom";
import ProgressBar from 'react-bootstrap/ProgressBar';

export default class BasicVis extends React.Component {
  state = {
    metrics : [],
  }
  componentDidMount() {
    const jwt = JSON.parse(localStorage.getItem('jwt'));
    axios.post(process.env.REACT_APP_API_ENDPOINT+'/api/request_metrics/', { jwt: jwt["jwt"] })
      .then((result) => {
        var jresp = JSON.parse(result.data)
        console.log("Data resp");
        console.log(jresp);
        this.setState({ metrics: jresp });
      })
      .catch((error) => {
        this.setState({errorMessage: error.message});
        if (error.response) {
	  if (error.response.status == '401') {
	    this.setState({ error: 'auth' });
          } else if (error.request) {
            console.log("network error");
          } else {
            console.log("unhandled error " + error.response.status + ", " + error.response.data);
          }
	}
      });
  }

  render(){
    let {metrics, error} = this.state;
    let animated = false;
    if (metrics.percent_placed < 100) {
      animated = true;
    }
    //TODO(tb): omfg someone plz make this use a map or something
    return(
      <Container>
	    {error && (<Navigate to="/login" replace={true} />)}
        <Row className="justify-content-md-center">
          <Col width="100">
            <p></p>
   	        {animated ?
                 <ProgressBar animated now={this.state.metrics.percent_placed} label={`Percent placed ${this.state.metrics.percent_placed}%`} />
	         :
	             <ProgressBar now={this.state.metrics.percent_placed} label={`Percent placed ${this.state.metrics.percent_placed}%`} />
	        }
            <p></p>
          </Col>
        </Row>
        <Row className="justify-content-md-center">
          <Col xs lg="4">
              <h5> Guests</h5>
              <div className="card-subtitle mb-2 text-muted">Count: {this.state.metrics.guest_count}</div>
              <div className="card-subtitle mb-2 text-muted">Unique: {this.state.metrics.guest_unique}</div>
              <div className="card-subtitle mb-2 text-muted">Unplaced: {this.state.metrics.guest_unplaced}</div>
              <div className="card-subtitle mb-2 text-muted">Swaps Created: {this.state.metrics.rooms_swap_code_count}</div>
              <div className="card-subtitle mb-2 text-muted">Swaps Completed: {this.state.metrics.rooms_swap_success_count}</div>
          </Col>
          <Col xs lg="4">
              <h5> Rooms</h5>
              <div className="card-subtitle mb-2 text-muted">Count: {this.state.metrics.rooms_count}</div>
              <div className="card-subtitle mb-2 text-muted">Occupied: {this.state.metrics.rooms_occupied}</div>
              <div className="card-subtitle mb-2 text-muted">Available: {this.state.metrics.rooms_available}</div>
              <div className="card-subtitle mb-2 text-muted">Swappable: {this.state.metrics.rooms_swappable}</div>
              <div className="card-subtitle mb-2 text-muted">Manually Placed: {this.state.metrics.rooms_placed_manually}</div>
              <div className="card-subtitle mb-2 text-muted">RoomBot Placed: {this.state.metrics.rooms_placed_by_roombot}</div>
          </Col>
          <Col xs lg="4">
              <h5> Unoccupied</h5>
              <div className="card-subtitle mb-2 text-muted">Queens: {this.state.metrics.Queen_unoccupied} of {this.state.metrics.Queen_total} total</div>
              <div className="card-subtitle mb-2 text-muted">King: {this.state.metrics.King_unoccupied} of {this.state.metrics.King_total} total</div>
              <div className="card-subtitle mb-2 text-muted">KingSierraSuite: {this.state.metrics.King_Sierra_Suite_unoccupied} of {this.state.metrics.King_Sierra_Suite_total} total</div>
              <div className="card-subtitle mb-2 text-muted">QueenSierraSuite: {this.state.metrics.Queen_Sierra_Suite_unoccupied} of {this.state.metrics.Queen_Sierra_Suite_total} total</div>
              <div className="card-subtitle mb-2 text-muted">ExecutiveSuite: {this.state.metrics.Executive_Suite_unoccupied} of {this.state.metrics.Executive_Suite_total} total</div>
              <div className="card-subtitle mb-2 text-muted">TahoeSuite: {this.state.metrics.Tahoe_Suite_unoccupied} of {this.state.metrics.Tahoe_Suite_total} total</div>
              <div className="card-subtitle mb-2 text-muted">WeddingOffice: {this.state.metrics.Wedding_Office_unoccupied} of {this.state.metrics.Wedding_Office_total} total</div>
              <div className="card-subtitle mb-2 text-muted">Chapel: {this.state.metrics.Chapel_unoccupied} of {this.state.metrics.Chapel_total} total</div>
          </Col>
        </Row>
      </Container>
    )
  }
}
