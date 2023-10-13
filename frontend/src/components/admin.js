
import axios from 'axios';
import Accordion from 'react-bootstrap/Accordion';
import "../styles/RoombotAdmin.css";

import { useEffect, useState } from 'react';

import Button from 'react-bootstrap/Button';
import Spinner from 'react-bootstrap/Spinner';
import Card from 'react-bootstrap/Card';


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
      });
    }
  }, [isLoading]);
  return (
    <Card>
      <Card.Header>Load Guests</Card.Header>
      <Card.Body>
        <Card.Title>Using file:</Card.Title>
        <Card.Text>
         ../samples/exampleMainGuestList.csv 
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
  return (
    <Card>
      <Card.Header>Run Reports</Card.Header>
      <Card.Body>
        <Card.Title>Creating and emailing the following reports:</Card.Title>
        <Card.Text>
         '../output/diff_dump.md'
         '../output/roombaht_application.md'
         '../output/log_script_out.md'
         '../output/guest_dump.csv'
         '../output/room_dump.csv'
        </Card.Text>
        <Button variant="primary">Run</Button>
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
