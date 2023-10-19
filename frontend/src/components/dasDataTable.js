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
import ModalImage from "react-modal-image";
import {ModalRequestSwap} from "./modals.js";


const STORY_HEADERS: TableColumnType<ArrayElementType>[] = [
    {
      prop: "number",
      title: "Number",
      isSortable: true,
      isFilterable: true
    },
    {
      prop: "name_take3",
      title: "Type",
      isFilterable: true
    },
    {
      prop: "floorplan",
      title: "FloorPlan",
      cell: (row) => (
          <ModalImage
            small={"layouts/" + row.floorplans[1]}
            large={"layouts/" + row.floorplans[0]}
            alt="Babyface_footprint"
          />
      )
    },
    {
      prop: "button",
      cell: (row) => (
        <ModalRequestSwap row={row}/>
      )
    }
  ];


export default class RoomDataTable extends React.Component {
  state = {
    rooms : [],
    jwt: ""
  }

  componentDidMount() {
    const jwt = JSON.parse(localStorage.getItem('jwt'));
    console.log("ALL THE ROOMSSS");
    axios.post(process.env.REACT_APP_API_ENDPOINT+"/api/rooms/", {
            jwt: jwt["jwt"]
      })
      .then(res => {
        console.log(res.data);
        const data = res.data
        this.state.rooms = data
        this.setState({ data  });
      })
  }

  render(){
    return(
      <DatatableWrapper
        body={this.state.rooms}
        headers={STORY_HEADERS}
        paginationOptionsProps={{
          initialState: {
            rowsPerPage: 10,
            options: [5, 10, 15, 20]
          }
        }}
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
            <PaginationOptions />
          </Col>
          <Col
            xs={12}
            sm={6}
            lg={4}
            className="d-flex flex-col justify-content-end align-items-end"
          >
            <Pagination />
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
