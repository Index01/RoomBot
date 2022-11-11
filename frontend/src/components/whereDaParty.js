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
//import ModalImage from "react-modal-image";


const STORY_HEADERS: TableColumnType<ArrayElementType>[] = [
    {
      prop: "room_number",
      title: "Room Number",
      isSortable: true,
      isFilterable: true
    },
    {
      prop: "description",
      title: "Description",
      isFilterable: true
    },
    {
      prop: "end_time",
      title: "Party End Time",
//      cell: (row) => (
//          <ModalImage
//            small={row.floorplans[1]}
//            large={row.floorplans[0]}
//            alt="endtime"
//          />
//      )
    },
//    {
//      prop: "button",
//      cell: (row) => (
//	<Button disabled={row.available ? false : true}
//	  variant={row.available ? "outline-primary" : "outline-secondary"}
//          size="sm"
//          onClick={(e) => {
//            RequestSwap(row.number);
//          }}
//        >
//          SendSwapRequest
//        </Button>
//      )
//    }
  ];

export default class WhereDaParty extends React.Component {
  state = {
    rooms : [],
    jwt: ""
  }
  
  
  
  componentDidMount() {
    //const jwt = JSON.parse(localStorage.getItem('jwt'));
    //axios.post(process.env.BASE_URL+":8000/api/rooms/", {
    console.log(process.env.REACT_APP_BASE_URL)
    axios.get(process.env.REACT_APP_BASE_URL+":8000/api/iama_party/")
    //axios.get("http://192.168.132.25:8000/api/iama_party/")
          
      .then(res => {
        const data = res.data
        console.log(data);
       // const data = JSON.parse(res.data)
       // console.log(JSON.parse(JSON.stringify(data)));
        this.state.rooms = data
        this.setState({ data  });

      })
  }


  render(){
    return(
      <DatatableWrapper
        //body={arr}
        body={this.state.rooms}
        headers={STORY_HEADERS}
      >
        <Row className="mb-4 p-2">
          <Col
            xs={12}
            lg={4}
            className="d-flex flex-col justify-content-end align-items-end"
          >
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
