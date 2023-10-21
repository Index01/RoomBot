
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import axios from 'axios';
import React from "react";
import { Navigate } from "react-router-dom";

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
    return(
      <Container>
	{error && (<Navigate to="/login" replace={true} />)}
	{metrics &&
        <Row>
            <p></p>
          <Col>
              <div className="card-subtitle mb-2 text-muted">Guest Count: {this.state.metrics.guest_count}</div>
          </Col>
          <Col>
              <div className="card-subtitle mb-2 text-muted">Guest Unique: {this.state.metrics.guest_unique}</div>
          </Col>
          <Col>
              <div className="card-subtitle mb-2 text-muted">Room Count: {this.state.metrics.rooms_count}</div>
          </Col>
          <Col>
              <div className="card-subtitle mb-2 text-muted">Room Occupied: {this.state.metrics.rooms_occupied}</div>
          </Col>
          <Col>
              <div className="card-subtitle mb-2 text-muted">Room Swappable: {this.state.metrics.rooms_swappable}</div>
          </Col>
        </Row>}
      </Container>
    )
  }
}
