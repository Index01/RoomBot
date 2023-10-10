
import axios from 'axios';
import Accordion from 'react-bootstrap/Accordion';
import "../styles/RoombotAdmin.css";

import Button from 'react-bootstrap/Button';
import Card from 'react-bootstrap/Card';

const AdminLoadRooms = (evt) => {
        console.log(evt);
        const jwt = JSON.parse(localStorage.getItem('jwt'));
        const guest = {
            jwt: jwt["jwt"],
        }
        axios.post(process.env.REACT_APP_DJANGO_ENDPOINT+'/api/admin_load_rooms/', { guest })
          .then(res => {
            console.log(res.data);
          })
          .catch((error) => {
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

function RoomsCard() {
  return (
    <Card>
      <Card.Header>Load Rooms</Card.Header>
      <Card.Body>
        <Card.Title>Using file:</Card.Title>
        <Card.Text>
         ../samples/exampleRoomsList.csv 
        </Card.Text>
        <Button variant="primary"
          onClick={(e) => {
            AdminLoadRooms();
          }}>Load</Button>
      </Card.Body>
    </Card>
  );
}

function GuestsCard() {
  return (
    <Card>
      <Card.Header>Load Guests</Card.Header>
      <Card.Body>
        <Card.Title>Using file:</Card.Title>
        <Card.Text>
         ../samples/exampleGuestsList.csv 
        </Card.Text>
        <Button variant="primary">Load</Button>
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
          <RoomsCard />
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
