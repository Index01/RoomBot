
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

const CreateSwapCode = (evt) => {
        console.log(evt);
        const jwt = JSON.parse(localStorage.getItem('jwt'));
        axios.post(`http://192.168.4.24:8000/api/swap_gen/`, {
        //axios.post(process.env.REACT_APP_DJANGO_IP+":8000/api/rooms/", {
                jwt: jwt,
                number: evt,
          })
          .then(res => {
            const phrase = JSON.parse(res.data)["swap_phrase"];
            //localStorage.setItem('jwt', res.data);
            //window.location = "/rooms";
            alert(`Send this code to your friend if u rly want to swap roomz with them. You will need to checkin at the front desk within the hr.\n\nThis code is good for 10mins\nNo un-swapzies.\n\nSwap Code: ${phrase}`);
    
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

const SendSwapCode = (evt) => {

}

const EnterSwapCode = (evt) => {
        console.log(evt);
        const code = prompt(`Enter your friends swap code to swap this room with theirs.`);
        console.log(code);
        const jwt = JSON.parse(localStorage.getItem('jwt'));
        axios.post(`http://192.168.4.24:8000/api/swap_it_up/`, {
        //axios.post(process.env.REACT_APP_DJANGO_IP+":8000/api/rooms/", {
                jwt: jwt,
                number: evt,
                swap_code: code
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
      prop: "type",
      title: "RoomType",
    },
    {
      prop: "number",
      title: "RoomNumber",
      isSortable: true,
    },
    {
      prop: "button",
      cell: (row) => (
        <Button
          variant="outline-primary"
          size="sm"
          onClick={(e) => {
            CreateSwapCode(row.number);
          }}
        >
          CreateSwapCode
        </Button>
      )
    },
    {
      prop: "button",
      cell: (row) => (
        <Button
          variant="outline-primary"
          size="sm"
          onClick={(e) => {
            EnterSwapCode(row.number);
          }}
        >
          EnterSwapCode
        </Button>
      )
    }
  ];

export default class MyRoomsTable extends React.Component {
  state = {
    rooms : [],
    jwt: ""
  }
  
  
  
  //let arr = new Array();
  componentDidMount() {
    //axios.get(`http://192.168.4.24:8000/api/rooms/`)
    //  .then(res => {
    //    //console.log(res.data);
    //    //arr.push(res.data)
    //    //res.data.forEach(elem => arr.push(elem))
    //    //const jwt = JSON.parse(localStorage.getItem('jwt'));
    //    //console.log(jwt);
    //    const data = res.data
    //    this.state.rooms = data
    //    this.setState({ data  });
    //    console.log(this.state.rooms);
    //  })


    const jwt = JSON.parse(localStorage.getItem('jwt'));
    axios.post(`http://192.168.4.24:8000/api/my_rooms/`, {
    //axios.post(process.env.REACT_APP_DJANGO_IP+":8000/api/rooms/", {
            jwt: jwt
      })
      .then(res => {
        //console.log(res.data);
        //window.location = "/rooms";
        const data = JSON.parse(res.data)
        //console.log(JSON.parse(JSON.stringify(data)));
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
