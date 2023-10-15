
import axios from 'axios';
import Accordion from 'react-bootstrap/Accordion';
import "../styles/RoombotAdmin.css";
import { useEffect, useState } from 'react';
import Button from 'react-bootstrap/Button';
import Spinner from 'react-bootstrap/Spinner';
import Card from 'react-bootstrap/Card';
import ListGroup from 'react-bootstrap/ListGroup';


function GuestsCard() {
  const [isLoading, setLoading] = useState(false);
  const handleClick = () => setLoading(true);
  const jwt = JSON.parse(localStorage.getItem('jwt'));
  const data = {
      jwt: jwt["jwt"],
  }
  useEffect(() => {
    if (isLoading) {
       axios.post(process.env.REACT_APP_API_ENDPOINT+'/api/create_guests/', { data }).then((res) => {
        console.log(res.data);
        setLoading(false);
      })
      .catch((error) => {
        console.log(error.response);
        setLoading(false);
        window.location = "/rooms"
      });
    }
  }, [isLoading]);
  return (
    <Card>
      <Card.Header>Load Guests</Card.Header>
      <Card.Body>
        <Card.Title>Using file:</Card.Title>
        <Card.Text>
         ../samples/exampleGuestList.csv 
        </Card.Text>

        <Button
          variant="primary"
          disabled={isLoading}
          onClick={!isLoading ? handleClick : null}
        >
          {isLoading ? 'Loading…' : 'Click to load'}
        </Button>

      </Card.Body>
    </Card>
  );
}


function ReportCard() {
  const [isLoading, setLoading] = useState(false);
  const [respText, setRespText] = useState([]);
  const handleClick = () => setLoading(true);
  const jwt = JSON.parse(localStorage.getItem('jwt'));
  const data = {
      jwt: jwt["jwt"],
  }
  useEffect(() => {
    if (isLoading) {
       axios.post(process.env.REACT_APP_API_ENDPOINT+'/api/run_reports/', { data })
         .then((respText) => {
           console.log(JSON.parse(respText.data).admins);
           setLoading(false);
           setRespText(JSON.parse(respText.data).admins);
         })
         .catch((error) => {
           setLoading(false);
         });
    }
  }, [isLoading]);
  return (
    <Card>
      <Card.Header>Run reports</Card.Header>
      <Card.Body>
        <Card.Title>Run the following reports:</Card.Title>
        <ListGroup variant="flush">
          <ListGroup.Item>../output/diff_dump.md</ListGroup.Item>
          <ListGroup.Item>../output/roombaht_application.md</ListGroup.Item>
          <ListGroup.Item>../output/log_script_out.md</ListGroup.Item>
          <ListGroup.Item>../output/guest_dump.csv</ListGroup.Item>
          <ListGroup.Item>../output/room_dump.csv</ListGroup.Item>
        </ListGroup>

        <ol className="card-subtitle mb-2 text-muted">
          {respText.map((item) => (
            <li key={item}>Sent email to: {item}</li>
          ))}
        </ol>

        <Button
          variant="primary"
          disabled={isLoading}
          onClick={!isLoading ? handleClick : null}
        >
          {isLoading ? 'Running…' : 'Click to run'}
        </Button>

      </Card.Body>
    </Card>
  );
}


function RoombotAdmin() {
  return (
    <Accordion defaultActiveKey="0">
      <Accordion.Item eventKey="0">
        <Accordion.Header>Load Rooms & Guests</Accordion.Header>
        <Accordion.Body>
          <div>
          <GuestsCard />
          </div>
        </Accordion.Body>
      </Accordion.Item>
      <Accordion.Item eventKey="1">
        <Accordion.Header>Run Reports</Accordion.Header>
        <Accordion.Body>
          <div>
          <ReportCard />
          </div>
        </Accordion.Body>
      </Accordion.Item>
    </Accordion>
  );
}

export default RoombotAdmin;
