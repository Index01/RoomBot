import RoomDataTable from '../components/dasDataTable.js';
import MyRoomsTable from '../components/myRooms.js';
import "../styles/RoomDataTable.css";
import React from 'react';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';


const RoomSelekta = () => {
    return(
        <div className="componentContainer">

            <div className="AppHeader">
	         <img src="roombaht_header.png" alt="RoomBaht9000" />
            </div>
             
            <div className="DTApp">
              <Row className="justify-content-md-center">
                <Col xs lg="6">
                  <h1>Donate</h1>
                  <p></p>
                  <h4>Luving your RS Roombaht experience? </h4>
                  <h6>Consider contributing. Money.</h6>
                  <p></p>
                </Col>
              </Row>

              <Row className="justify-content-md-center">
                <Col xs lg="6">

                    <div className="card-subtitle mb-2 text-muted">
                        <p>
                        This application is primarily powered by magical woodland creatures. Plus a few very fashionable engineers. Consider contributing some coins so these mythical creatures can continue to exist. 
                        </p>
                    </div>
                </Col>
              </Row>

              <Row className="justify-content-md-center">
                <Col xs lg="6">
                  <p></p>
                  <h4>
                  <a href="https://account.venmo.com/u/tyler32bit">Venmo</a>
            :
                  Tyler32bit@venmo.com
                  </h4>
                  <p></p>

                    <div className="card-subtitle mb-2 text-muted">
                        <p>
                         Add some fun emojis to the description, so we know u r not a robot. unless u r a robot. in which case send robot emojis.
                        </p>
                    </div>
                </Col>
              </Row>

            </div>
        </div>
    );
};

export default RoomSelekta;
