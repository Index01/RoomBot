
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import axios from 'axios';
import React from "react";


export default class BasicVis extends React.Component {
  state = {
    metrics : [],
  }
  componentDidMount() {
    const jwt = JSON.parse(localStorage.getItem('jwt'));
    const data = {
        jwt: jwt["jwt"],
    }
    axios.post(process.env.REACT_APP_API_ENDPOINT+'/api/request_metrics/', { data })
      .then((result) => {
        var jresp = JSON.parse(result.data)
        console.log("Data resp");
        console.log(jresp);
        this.setState({ metrics: jresp });
      })
      .catch((error) => {
        this.setState({errorMessage: error.message});
        if (error.response) {
          console.log("server responded");
          console.log(error.response);
        } else {
          console.log(error);
        }
      });
  }


  render(){
    const {metrics} = this.state;
    return(
      <Container>
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
        </Row>
      </Container>
    )
  }
}
