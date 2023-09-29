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


const RequestSwap = (evt) => {
        const contacts = prompt("Ok fam so rly we can only do so much for you here. We can send the owner of this room an email with your contact info, try to put you in touch, but we cant make them look at their phone or care about trading rooms with you. So. If you have another way of reaching this person go for it.\n\nOnce you are in contact, click the CreateSwapCode button on your room. Send the code and have them enter it.\n\nEnter your email addres or phone number for the room owner to reach you:");
        if (contacts === null) {
            return; 
        }
        console.log(evt);
        const jwt = JSON.parse(localStorage.getItem('jwt'));
        const guest = {
            jwt: jwt["jwt"],
            number: evt,
	    contact_info: contacts
        }
        axios.post(process.env.REACT_APP_DJANGO_ENDPOINT+'/api/swap_request/', { guest })
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
            small={row.floorplans[1]}
            large={row.floorplans[0]}
            alt="Babyface_footprint"
          />
      )
    },
    {
      prop: "button",
      cell: (row) => (
	<Button disabled={row.available ? false : true}
	  variant={row.available ? "outline-primary" : "outline-secondary"}
          size="sm"
          onClick={(e) => {
            RequestSwap(row.number);
          }}
        >
          SendSwapRequest
        </Button>
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
    console.log(process.env.REACT_APP_DJANGO_ENDPOINT+"/api/rooms/");
    axios.post(process.env.REACT_APP_DJANGO_ENDPOINT+"/api/rooms/", {
            jwt: jwt["jwt"]
      })
      .then(res => {
        console.log(res.data);
        const data = res.data
        //console.log(JSON.parse(JSON.stringify(data)));

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
