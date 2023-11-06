import RoomDataTable from '../components/dasDataTable.js';
import MyRoomsTable from '../components/myRooms.js';
import "../styles/RoomDataTable.css";
import React from 'react';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import { Toaster } from 'react-hot-toast';

const RoomSelekta = () => {
    return(
        <div className="componentContainer">

            <div className="AppHeader">
	         <img src="roombaht_header.png" alt="RoomBaht9000" />
            </div>

            <div className="DTApp"> My Rooms
              <MyRoomsTable/>
            </div>

            <div className="DTApp"> Swappable Rooms
              <RoomDataTable/>
            </div>

            <div className="DTApp">
              <Row>
                <Col>
                  <a href="/donate">Donate to the Roombaht project</a>
                </Col>
                <Col xs="auto">
                  <div className="text-muted">
                     Contact support: placement@take3presents.com
                  </div>
                </Col>
              </Row>

            </div>
            <Toaster />
        </div>
    );
};

export default RoomSelekta;
