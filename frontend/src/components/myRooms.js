
import "bootstrap/dist/css/bootstrap.css";
import { Button, Col, Row, Table } from "react-bootstrap";
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
import React from "react";
import { ModalEnterCode, ModalCreateCode } from "./modals.js";
import Modal from 'react-bootstrap/Modal';
import { useState } from 'react';
import { Navigate } from "react-router-dom";

export default class MyRoomsTable extends React.Component {
  state = {
    rooms : [],
    jwt: "",
    refreshTimer: null
  }

  loadMyRooms() {
    const jwt = JSON.parse(localStorage.getItem('jwt'));
    if (jwt === null) {
      this.setState({error: 'auth'});
      return;
    }
    axios.post(window.location.protocol + "//" + window.location.hostname + ":8000/api/my_rooms/", {
      jwt: jwt["jwt"]
    })
      .then(res => {
        const data = JSON.parse(res.data)
        console.log(JSON.parse(JSON.stringify(data)));
        this.state.rooms = data.rooms;
	this.state.swaps_enabled = data.swaps_enabled;
        this.setState({ data });
	if ( this.state.swaps_enabled && this.state.refreshTimer === null ) {
	  this.state.refreshTimer = setInterval(() => {
	    this.loadMyRooms();
	  }, 5000);
	}
      })
      .catch((error) => {
        this.setState({errorMessage: error.message});
        if (error.response) {
	  if (error.response.status === 401) {
	    this.setState({error: 'auth'});
	  } else {
	    console.log(error.response);
	    console.log("server responded");
	  }
        } else if (error.request) {
          console.log("network error");
        } else {
          console.log(error);
        }
      });
  }

  storyHeaderFactory(swaps_enabled) {
    let STORY_HEADERS: TableColumnType<ArrayElementType>[] = [
        {
          prop: "number",
          title: "Number",
          isSortable: true,
        },
        {
          prop: "type",
          title: "Type",
        },
        {
          prop: "button",
          cell: (row) => (
            <ModalCreateCode row={row} swaps_enabled={swaps_enabled} onExited={() => this.loadMyRooms() }/>
          )
        },
        {
          prop: "button",
          cell: (row) => (
            <ModalEnterCode row={row} swaps_enabled={swaps_enabled} onExited={() => this.loadMyRooms() }/>
          )
        },
      ];
    return STORY_HEADERS;
  };

  componentDidMount() {
    this.loadMyRooms();
  }

  render(){
    let {error} = this.state;
    return(
      <DatatableWrapper
        body={this.state.rooms}
        headers={this.storyHeaderFactory(this.state.swaps_enabled)}
      >
	{error && (<Navigate to="/login" replace={true} />)}
        <Row className="mb-4 p-2">
          <Col
            xs={12}
            lg={4}
            className="d-flex flex-col justify-content-end align-items-end"
          >
            <Filter />
          </Col>
          <Col
            xs={12}
            sm={6}
            lg={4}
            className="d-flex flex-col justify-content-lg-center align-items-center justify-content-sm-start mb-2 mb-sm-0"
          >
          </Col>
          <Col
            xs={12}
            sm={6}
            lg={4}
            className="d-flex flex-col justify-content-end align-items-end"
          >
          </Col>
        </Row>
        <Table>
          <TableHeader />
          <TableBody />
        </Table>
      </DatatableWrapper>
    )
  }
}
