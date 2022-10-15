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

const ReserveRoom = (evt) => {
        console.log(evt);
        const jwt = JSON.parse(localStorage.getItem('jwt'));
        axios.post(`http://192.168.4.24:8000/api/rooms/`, {
        //axios.post(process.env.REACT_APP_DJANGO_IP+":8000/api/rooms/", {

                jwt: jwt,
                number: evt 
          })
          .then(res => {
            console.log(res.data);
            //localStorage.setItem('jwt', res.data);
            //window.location = "/rooms";
    
          })
          .catch((error) => {
            //this.setState({errorMessage: error.message});
            //errorMessage = error.mesage;
            if (error.response) {
              console.log(error.response);
              console.log("server responded");
              //setErrorMessage("Example error message!")
              //errorMessage = "Failure to Login, fam!";
              //errorFlag = true; 
            } else if (error.request) {
              console.log("network error");
            } else {
              console.log(error);
            }
          });
}


const STORY_HEADERS: TableColumnType<ArrayElementType>[] = [
    {
      prop: "name_take3",
      title: "Take3Name",
      isFilterable: true
    },
    {
      prop: "name_hotel",
      title: "HotelName"
    },
    {
      prop: "number",
      title: "RoomNumber",
      isSortable: true,
      isFilterable: true
    },
    {
      prop: "available",
      title: "Available"
    },
    {
      prop: "score",
      title: "Stuff"
    },
    {
      prop: "button",
      cell: (row) => (
        <Button
          variant="outline-primary"
          size="sm"
          onClick={(e) => {
            alert(`Room number:${row.number} will be reserved in your name. \nYou will need to checkin at the front desk`);
            ReserveRoom(row.number);
          }}
        >
          SelectRoom
        </Button>
      )
    }
  ];

export default class RoomDataTable extends React.Component {
  state = {
    rooms : [],
    jwt: ""
  }
  
  
  
  //let arr = new Array();
  componentDidMount() {
    axios.get(`http://192.168.4.24:8000/api/rooms/`)
    //console.log(process.env.REACT_APP_DJANGO_IP+":8000/api/login/");
    //axios.get(process.env.REACT_APP_DJANGO_IP+":8000/api/rooms/")
      .then(res => {
        //console.log(res.data);
        //arr.push(res.data)
        //res.data.forEach(elem => arr.push(elem))
        //const jwt = JSON.parse(localStorage.getItem('jwt'));
        //console.log(jwt);
        const data = res.data
        this.state.rooms = data
        this.setState({ data  });
        //console.log(data);
        console.log(this.state.rooms);
      })
  }


  render(){
    return(
      <DatatableWrapper
        //body={arr}
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
