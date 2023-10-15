
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


const STORY_HEADERS: TableColumnType<ArrayElementType>[] = [
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
        <ModalCreateCode row={row.number}/>
      )
    },
    {
      prop: "button",
      cell: (row) => (
        <ModalEnterCode row={row.number}/>
      )
    },
  ];

export default class MyRoomsTable extends React.Component {
  state = {
    rooms : [],
    jwt: ""
  }


  componentDidMount() {
    const jwt = JSON.parse(localStorage.getItem('jwt'));
    axios.post(process.env.REACT_APP_API_ENDPOINT+'/api/my_rooms/', {
            jwt: jwt["jwt"]
      })
      .then(res => {
        const data = JSON.parse(res.data)
        console.log(JSON.parse(JSON.stringify(data)));
        this.state.rooms = data
        this.setState({ data  });

      })
      .catch((error) => {
        this.setState({errorMessage: error.message});
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


  render(){
    return(
      <DatatableWrapper
        body={this.state.rooms}
        headers={STORY_HEADERS}
      >
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
