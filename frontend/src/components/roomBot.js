import React from 'react';
import axios from 'axios';

export default class RoomList extends React.Component {
//  const config = {
//    headers:{
//      "Access-Control-Allow-Origin": "*"
//    }
//  };
        
  state = {
    rooms: []
  }


  componentDidMount() {
  //const fs = require('browserify-fs');
    axios.get(`http://127.0.0.1:8000/api/rooms/`)
      .then(res => {
        //console.log(res.data);
        const rooms = res.data;
        this.setState({ rooms });
        //fs.writeFile('response.json', JSON.stringify(res.data), function (err) {
        //    console.log(err);
        //});
      })
  }

  render() {
    return (
      <ul>
        {
          this.state.rooms
            .map(room =>
              <li key={room.name_hotel}>{room.name_take3}</li>
            )
        }
      </ul>
    )
  }
}
