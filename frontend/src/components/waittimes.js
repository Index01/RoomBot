import "bootstrap/dist/css/bootstrap.css";
import "../styles/modals.css";
import { Col, Row, Table } from "react-bootstrap";
import {
  DatatableWrapper,
  Filter,
  Pagination,
  PaginationOptions,
  TableBody,
  TableColumnType,
  TableHeader
} from "react-bs-datatable";
import axios from 'axios';
import "../styles/RoombotAdmin.css";
import Button from 'react-bootstrap/Button';
import React from "react";
import Modal from 'react-bootstrap/Modal';
import Form from 'react-bootstrap/Form';
import toast, { Toaster } from 'react-hot-toast';

function ModalEdit(props) {
  state = {
    show: false
  };
  const [show, setShow] = useState(false);
  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);
  const loadWait = (short_name) => {
    const wait_url = window.location.protocol + "//" + window.location.hostname + ":8080/api/wait/" + short_name;
    axios.get(wait_url)
      .then(res => {
	console.log("Loaded, lol");
      })
  };
  return(
      <>
      <Button variant={"outline-primary"} size="sm" onclick={startEdit}>
        Edit Waittime
      </Button>
      <Modal show={show} onHide={handleClose}>
        <Modal.Header closeButton>
          <Modal.Title>Edit Waittime: {props.name}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3" controlId="exampleForm.ControlTextarea1">
              <Form.Label>The Wait Time Is</Form.Label>
              <Form.Control type="text" name="inputWaitTime" />
            </Form.Group>
            <Form.Group className="mb-3" controlId="exampleForm.ControlTextarea1">
              <Form.Label>Password</Form.Label>
              <Form.Control type="text" name="inputPassword" />
            </Form.Group>
            <Button variant="primary" type="submit">
              Submit
            </Button>
          </Form>
        </Modal.Body>
      </Modal>
      </>
  )
}


export default class HowLongTho extends React.Component {
  state = {
    waittimes: []
  };

  waitHeaderFactory() {
    let WAIT_HEADERS: TableColumnType<ArrayElementType>[] = [
      {
	prop: "name",
	title: "Name"
      },
      {
	prop: "button",
	cell: (row) => ( <ModalEdit short_name={row.short_name} /> )
      }
    ];
    return WAIT_HEADERS;
  }
  render(){
    return(
      <div>
	<DatatableWrapper body={this.state.waittimes} headers={this.waitHeaderFactory()}>
	  <Row classname="mb-4 p-2">
	    <Col xs={12} lg={4} className="d-flex flex-col justify-content-end align-items-end" />
	  </Row>
	  <Table>
	    <TableHeader />
	    <TableBody />
	  </Table>
	</DatatableWrapper>
      </div>
    );
  }
}
