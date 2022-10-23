
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

const IAmAParty = (evt) => {
        const duration = prompt("\n\nDo you want to let ppl know they can stop by?\nDon't mind making new friends?\n\nEnter the number of hours your would like to be listed as a ppaaarrtaay.\n");
        const jwt = JSON.parse(localStorage.getItem('jwt'));
        axios.post(`http://ec2-3-21-92-196.us-east-2.compute.amazonaws.com:8000/api/i_am_party/`, {
                jwt: jwt['jwt'],
                number: evt,
                duration: duration,
          })
          .then(res => {
            const duration_remaining = JSON.parse(res.data)["swap_phrase"];
	    console.log(duration_remaining);
          })
          .catch((error) => {
            //this.setState({errorMessage: error.message});
            //errorMessage = error.mesage;
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


const CreateSwapCode = (evt) => {
        console.log(evt);
        const jwt = JSON.parse(localStorage.getItem('jwt'));
        axios.post(`http://ec2-3-21-92-196.us-east-2.compute.amazonaws.com:8000/api/swap_gen/`, {
        //axios.post(process.env.REACT_APP_DJANGO_IP+":8000/api/rooms/", {
                jwt: jwt['jwt'],
                number: evt,
          })
          .then(res => {
            const phrase = JSON.parse(res.data)["swap_phrase"];
            alert(`Send this code to your friend if u rly want to swap roomz with them. You will need to checkin at the front desk within the hr.\n\nThis code is good for 10mins\nNo un-swapzies.\n\nSwap Code: ${phrase}`);
          })
          .catch((error) => {
            //this.setState({errorMessage: error.message});
            //errorMessage = error.mesage;
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


const EnterSwapCode = (evt) => {
        console.log(evt);
        const code = prompt(`Enter your friends swap code to swap this room with theirs.`);
        console.log(code);
        const jwt = JSON.parse(localStorage.getItem('jwt'));
        axios.post(`http://ec2-3-21-92-196.us-east-2.compute.amazonaws.com:8000/api/swap_it_up/`, {
        //axios.post(process.env.REACT_APP_DJANGO_IP+":8000/api/rooms/", {
                jwt: jwt['jwt'],
                number: evt,
                swap_code: code
          })
          .then(res => {
            console.log(res.data);
          })
          .catch((error) => {
            //this.setState({errorMessage: error.message});
            //errorMessage = error.mesage;
            if (error.response) {
              console.log(error.response);
              console.log("server responded");
              //errorMessage = "Failure to Login, fam!";
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
    },
    {
      prop: "type",
      title: "Type",
    },
    {
      prop: "button",
      cell: (row) => (
        <Button
          variant="outline-info"
          size="sm"
          onClick={(e) => {
            IAmAParty(row.number);
          }}
        >
          IAmAParty
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
  
  
  componentDidMount() {
    const jwt = JSON.parse(localStorage.getItem('jwt'));
    axios.post(`http://ec2-3-21-92-196.us-east-2.compute.amazonaws.com:8000/api/my_rooms/`, {
    //axios.post(process.env.REACT_APP_DJANGO_IP+":8000/api/rooms/", {
            jwt: jwt["jwt"]
      })
      .then(res => {
        //console.log(res.data);
        //window.location = "/rooms";
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
