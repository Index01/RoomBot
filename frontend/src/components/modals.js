
import React, { useState, useEffect } from 'react';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import axios from 'axios';
import toast, { Toaster } from 'react-hot-toast';
import "../styles/modals.css";
const swapError = (msg) => toast.error("Swap error: " + msg);

export function ModalRequestSwap(props) {
  const [show, setShow] = useState(false);
  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);
  const [phrase, setPhrase] = useState("");
  const jwt = JSON.parse(localStorage.getItem('jwt'));
  const row = props.row;
  const handleAPICall = (contacts) => {
    if (contacts === null) {
        return;
    }
    axios.post(process.env.REACT_APP_API_ENDPOINT+'/api/swap_request/', {
        jwt: jwt["jwt"],
        number: row.number,
	    contact_info: contacts
    })
      .then(res => {
	toast.success("Swap request sent.");
      })
      .catch((error) => {
        if (error.response) {
	  if ( error.response.status == 400 ) {
	    swapError("Unacceptable swap requested")
	  } else {
            console.log("server responded");
            console.log(error.response.data);
	    swapError("Server responded with error. contact placement@take3presents.com");
	  }
        } else if (error.request) {
	  swapError("Network error. Please try again later.");
        } else {
	  swapError("Mysterious error is mysterious.");
          console.log(error);
        }
      });
  }

  const handleSubmit = (evt) => {
    evt.preventDefault();
    const formData = new FormData(evt.target),
      formDataObj = Object.fromEntries(formData.entries())
      handleAPICall(formDataObj.inputSwapCode);

  };

  return (
    <>
      {props.swaps_enabled ?
      <Button disabled={row.available ? false : true}
	    variant={row.available ? "outline-primary" : "outline-secondary"}
            size="sm"
            onClick={handleShow}>
            SendSwapRequest
      </Button>
       :
       <Button hidden disabled={row.available ? false : true}
	    variant={row.available ? "outline-primary" : "outline-secondary"}
            size="sm"
            onClick={handleShow}>
            SendSwapRequest
      </Button>
      }
      <Modal show={show} onHide={handleClose}>
        <Modal.Header closeButton>
          <Modal.Title>RoomService Room Trader</Modal.Title>
        </Modal.Header>
        <Modal.Body>

          <h5>System Live</h5>
          <p>Ok fam so rly we can only do so much for you here.</p>
          <p>We can send the owner of this room an email with your contact info, but we can’t make them look at their phone or want to swap rooms with you. So. If you have another way of reaching this person, go for it.</p>
          <p>Once you are in contact and both agree to the swap, click the CreateSwapCode button on your room. Send the code to the other person and have them enter it.</p>
          <p>Enter your email address and/or phone number so the owner of the room you want can contact you.</p>

          <Form onSubmit={handleSubmit}>

            <Form.Group className="mb-3" controlId="exampleForm.ControlTextarea1">
              <Form.Label>Your Contact Info:</Form.Label>
              <Form.Control type="text" name="inputSwapCode" />
            </Form.Group>

          <Button variant="primary" type="submit">
            Submit
          </Button>
          </Form>

        </Modal.Body>
        <Modal.Footer>
          {phrase}
        </Modal.Footer>
      </Modal>
    </>
  );
}


export function ModalEnterCode(props) {
  const [show, setShow] = useState(false);
  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);
  const [phrase, setPhrase] = useState("");
  const jwt = JSON.parse(localStorage.getItem('jwt'));
  const row = props.row.number;

  const handleAPICall = (code) => {
    axios.post(process.env.REACT_APP_API_ENDPOINT+'/api/swap_it_up/', {
        jwt: jwt['jwt'],
        number: row,
        swap_code: code
      })
      .then(res => {
        setPhrase(res.data);
        handleClose();
        window.location = "/rooms"
      })
      .catch((error) => {
        if (error.response) {
	  if ( error.response.status == 400 ) {
	    swapError("Unacceptable swap requested")
	  } else {
            console.log("server responded");
            console.log(error.response.data);
	    swapError("Server responded with error. contact placement@take3presents.com");
	  }
        } else if (error.request) {
	  swapError("Network error. Please try again later.");
        } else {
	  swapError("Mysterious error is mysterious.");
          console.log(error);
        }
      });
  }

  const handleSubmit = (evt) => {
    evt.preventDefault();
    const formData = new FormData(evt.target),
      formDataObj = Object.fromEntries(formData.entries())
      handleAPICall(formDataObj.inputSwapCode);

  };

  return (
    <>
      {props.swaps_enabled ?
       <Button disabled={props.row.swappable ? false : true} size="sm" variant={props.row.swappable ? "outline-primary" : "outline-secondary"} onClick={handleShow}>
          EnterSwapCode
      </Button>
       :
      <Button hidden size="sm" variant="outline-primary" onClick={handleShow}>
          EnterSwapCode
      </Button>
      }

      <Modal show={show} onHide={handleClose}>
        <Modal.Header closeButton>
          <Modal.Title>RoomService Room Trader</Modal.Title>
        </Modal.Header>
        <Modal.Body>

          <h5>System Live</h5>
          <p>Be sure you want to trade this room with the one associated with the code you are about to enter. No take-backzies.</p>
          <Form onSubmit={handleSubmit}>

            <Form.Group className="mb-3" controlId="exampleForm.ControlTextarea1">
              <Form.Label>Input the SwapCode sent to you</Form.Label>
              <Form.Control type="text" name="inputSwapCode" />
            </Form.Group>

          <Button variant="primary" type="submit">
            Submit
          </Button>
          </Form>

        </Modal.Body>
        <Modal.Footer>
          {phrase}
        </Modal.Footer>
      </Modal>
    </>
  );
}

export function ModalCreateCode(props) {
  const [show, setShow] = useState(false);
  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);
  const [phrase, setPhrase] = useState("");

  const jwt = JSON.parse(localStorage.getItem('jwt'));
  const row = props.row.number;
  const handleAPICall = () => {

    axios.post(process.env.REACT_APP_API_ENDPOINT+'/api/swap_gen/', {
            jwt: jwt['jwt'],
            number: {row},
      })
      .then(res => {
        const phrase = JSON.parse(res.data)["swap_phrase"];
        setPhrase(phrase);
        handleShow();
      })
      .catch((error) => {
        if (error.response) {
	  if ( error.response.status == 400 ) {
	    swapError("Unacceptable swap requested")
	  } else {
            console.log("server responded");
            console.log(error.response.data);
	    swapError("Server responded with error. contact placement@take3presents.com");
	  }
        } else if (error.request) {
	  swapError("Network error. Please try again later.");
        } else {
	  swapError("Mysterious error is mysterious.");
          console.log(error);
        }
      });
  }


  return (
    <>
      {props.swaps_enabled ?
       <Button disabled={props.row.swappable ? false : true} size="sm" variant={props.row.swappable ? "outline-primary" : "outline-secondary"} onClick={handleAPICall}>
          CreateSwapCode
      </Button>
       :
      <Button hidden size="sm" variant="outline-primary" onClick={handleAPICall}>
          CreateSwapCode
      </Button>
      }

      <Modal show={show} onHide={handleClose}>

        <Modal.Header closeButton>
          <Modal.Title>RoomService Swapcode Generator</Modal.Title>
        </Modal.Header>

        <Modal.Body>
          <h5>Send this code to your friend if u rly want to trade roomz with them.</h5>
          <p/>
          <p>Direct them to follow the link in the request email, or initial placement email. Have them click EnterSwapCode on the room they are trading to you.</p>
          <p>This code expires after 10mins. No un-swapzies.</p>
          <p>Swap Code: {phrase}</p>
        </Modal.Body>

        <Modal.Footer>
          <Button variant="primary" onClick={handleClose}>
            Close
          </Button>
        </Modal.Footer>

      </Modal>
    </>
  );
}


