
import axios from 'axios';
import Accordion from 'react-bootstrap/Accordion';
import "../styles/RoombotAdmin.css";
import { useEffect, useState } from 'react';
import Button from 'react-bootstrap/Button';
import Spinner from 'react-bootstrap/Spinner';
import Card from 'react-bootstrap/Card';
import ListGroup from 'react-bootstrap/ListGroup';
import Form from 'react-bootstrap/Form';
import toast, { Toaster } from 'react-hot-toast';
const notifyOK = (msg) => toast.success(msg);
const notifyError = (msg) => toast.error("Error: " + msg);

function GuestsCard() {
  const [phrase, setPhrase] = useState("");
  const [respText, setRespText] = useState([]);
  const [isLoading, setLoading] = useState(false);
  const handleClick = () => setLoading(true);
  const jwt = JSON.parse(localStorage.getItem('jwt'));

  const handleAPICall = (file) => {
    if (jwt == null) {
      return;
    }
    const guest = {
        jwt: jwt["jwt"],
        guest_list: file,
    }
    axios.post(process.env.REACT_APP_API_ENDPOINT+'/api/guest_upload/', guest )
      .then(res => {
        setPhrase(res.data);
	notifyOK();
      })
      .catch((error) => {
        if (error.response) {
	  if (error.response.status == 400) {
	    notifyError("File is in wrong format.");
	  } else {
	    notifyError("Unable to upload file");
	  }
        } else if (error.request) {
	  notifyError("Network error!");
        } else {
	  notifyError("Mysterious error is mysterious.");
        }
      });
  };

  const handleSubmit = (evt) => {
    evt.preventDefault();
    const formData = new FormData(evt.target),
    formDataObj = Object.fromEntries(formData.entries())

    console.log(formDataObj.guestListUpload);

    const readUploadedFileAsText = (inputFile) => {
      const temporaryFileReader = new FileReader();

      return new Promise((resolve, reject) => {
        temporaryFileReader.onerror = () => {
          temporaryFileReader.abort();
          reject(new DOMException("Problem parsing input file."));
        };

        temporaryFileReader.onload = () => {
          resolve(temporaryFileReader.result);
        };
        temporaryFileReader.readAsText(inputFile);
      });
    };

    const handleUpload = async (file) => {

      try {
        const fileContents = await readUploadedFileAsText(file)
        handleAPICall(fileContents);
      } catch (e) {
        console.warn(e.message)
      }
    }
    handleUpload(formDataObj.guestListUpload);
  };

  useEffect(() => {
    if (isLoading) {
      axios.post(process.env.REACT_APP_API_ENDPOINT+'/api/create_guests/', { jwt: jwt['jwt'] }).then((res) => {
	notifyOK("Guests processed");
	setLoading(false);
        setRespText(JSON.parse(JSON.stringify(res.data)).results);
        setPhrase("");
      })
      .catch((error) => {
	notifyError("Unable to process guests");
        console.log(error);
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
         Select a guest list to upload, verify it, load it to database.
        </Card.Text>


        <Form onSubmit={handleSubmit}>
            <div className="mb-3">
              <input className="form-control" type="file" id="formFile" name="guestListUpload"></input>
            </div>
          <Button variant="primary" type="submit">
            Upload
          </Button>
        <p></p>
        <Card.Text>{phrase}</Card.Text>
        </Form>

        <Button
          variant="primary"
          disabled={isLoading}
          onClick={!isLoading ? handleClick : null}
        >
          {isLoading ? 'Loading…' : 'Click to load'}
        </Button>
        <p></p>
        <ul className="card-subtitle mb-2 text-muted">
          {respText.map(item =>
            <li key={item}>load response: {item}</li>
          )}
        </ul>


      </Card.Body>
    </Card>
  );
}


function ReportCard() {
  const [isLoading, setLoading] = useState(false);
  const [respText, setRespText] = useState([]);
  const handleClick = () => setLoading(true);
  const jwt = JSON.parse(localStorage.getItem('jwt'));
  useEffect(() => {
    if (jwt == null) {
      return;
    }
    const data = {
      jwt: jwt["jwt"],
    }
    if (isLoading) {
       axios.post(process.env.REACT_APP_API_ENDPOINT+'/api/run_reports/', data )
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
          <ListGroup.Item>Diff GuestList</ListGroup.Item>
          <ListGroup.Item>Diff Swaps</ListGroup.Item>
          <ListGroup.Item>Guest Dump</ListGroup.Item>
          <ListGroup.Item>Room Dump</ListGroup.Item>
          <ListGroup.Item>Hotel Exports</ListGroup.Item>
          <ListGroup.Item>Hotel Rooming Lists</ListGroup.Item>
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
