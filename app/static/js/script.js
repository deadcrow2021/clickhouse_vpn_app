let block = document.getElementById('wrapper')
let table_block = document.getElementById('records')


function make_fetch() {
    fetch('http://0.0.0.0:8000/anomalies/', {
      method: 'GET',
    }).then(
      response => response.json()
    ).then(result => {
      table_block.innerHTML =`
          <tr>
              <th>UUID</th>
              <th>User UUID</th>
              <th>Username</th>
          </tr>`
      Object.entries(result).forEach(element => {
        table_block.innerHTML += `
          <tr>
              <td>${element[0]}</td>
              <td>${element[1][0]}</td>
              <td>${element[1][1]}</td>
          </tr>`
      });
    })
}

setTimeout(make_fetch, 2000)

setInterval(make_fetch, 10000)