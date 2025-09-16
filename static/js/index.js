window.app = Vue.createApp({
  el: '#vue',
  mixins: [windowMixin],
  delimiters: ['${', '}'],
  data: function () {
    return {
      invoiceAmount: 10,
      qrValue: '',
      reccuring: [],
      reccuringTable: {
        columns: [
          {name: 'id', align: 'left', label: 'ID', field: 'id'},
          {name: 'name', align: 'left', label: 'Name', field: 'name'},
          {
            name: 'wallet',
            align: 'left',
            label: 'Wallet',
            field: 'wallet'
          },
          {
            name: 'total',
            align: 'left',
            label: 'Total sent/received',
            field: 'total'
          }
        ],
        pagination: {
          rowsPerPage: 10
        }
      },
      formDialog: {
        show: false,
        data: {},
        advanced: {}
      },
      urlDialog: {
        show: false,
        data: {}
      }
    }
  },

  ///////////////////////////////////////////////////
  ////////////////METHODS FUNCTIONS//////////////////
  ///////////////////////////////////////////////////

  methods: {
    async closeFormDialog() {
      this.formDialog.show = false
      this.formDialog.data = {}
    },
    async getReccurings() {
      await LNbits.api
        .request(
          'GET',
          '/reccuring/api/v1/reccuring',
          this.g.user.wallets[0].inkey
        )
        .then(response => {
          this.reccuring = response.data
        })
        .catch(err => {
          LNbits.utils.notifyApiError(err)
        })
    },
    async sendReccuringData() {
      const data = {
        name: this.formDialog.data.name,
        lnurlwithdrawamount: this.formDialog.data.lnurlwithdrawamount,
        lnurlpayamount: this.formDialog.data.lnurlpayamount
      }
      const wallet = _.findWhere(this.g.user.wallets, {
        id: this.formDialog.data.wallet
      })
      if (this.formDialog.data.id) {
        data.id = this.formDialog.data.id
        data.total = this.formDialog.data.total
        await this.updateReccuring(wallet, data)
      } else {
        await this.createReccuring(wallet, data)
      }
    },

    async updateReccuringForm(tempId) {
      const reccuring = _.findWhere(this.reccuring, {id: tempId})
      this.formDialog.data = {
        ...reccuring
      }
      if (this.formDialog.data.tip_wallet != '') {
        this.formDialog.advanced.tips = true
      }
      if (this.formDialog.data.withdrawlimit >= 1) {
        this.formDialog.advanced.otc = true
      }
      this.formDialog.show = true
    },
    async createReccuring(wallet, data) {
      data.wallet = wallet.id
      await LNbits.api
        .request('POST', '/reccuring/api/v1/reccuring', wallet.adminkey, data)
        .then(response => {
          this.reccuring.push(response.data)
          this.closeFormDialog()
        })
        .catch(error => {
          LNbits.utils.notifyApiError(error)
        })
    },

    async updateReccuring(wallet, data) {
      data.wallet = wallet.id
      await LNbits.api
        .request(
          'PUT',
          `/reccuring/api/v1/reccuring/${data.id}`,
          wallet.adminkey,
          data
        )
        .then(response => {
          this.reccuring = _.reject(this.reccuring, obj => obj.id == data.id)
          this.reccuring.push(response.data)
          this.closeFormDialog()
        })
        .catch(error => {
          LNbits.utils.notifyApiError(error)
        })
    },
    async deleteReccuring(tempId) {
      var reccuring = _.findWhere(this.reccuring, {id: tempId})
      const wallet = _.findWhere(this.g.user.wallets, {
        id: reccuring.wallet
      })
      await LNbits.utils
        .confirmDialog('Are you sure you want to delete this Reccuring?')
        .onOk(function () {
          LNbits.api
            .request(
              'DELETE',
              '/reccuring/api/v1/reccuring/' + tempId,
              wallet.adminkey
            )
            .then(() => {
              this.reccuring = _.reject(this.reccuring, function (obj) {
                return obj.id === reccuring.id
              })
            })
            .catch(error => {
              LNbits.utils.notifyApiError(error)
            })
        })
    },

    async exportCSV() {
      await LNbits.utils.exportCSV(this.reccuringTable.columns, this.reccuring)
    },
    async itemsArray(tempId) {
      const reccuring = _.findWhere(this.reccuring, {id: tempId})
      return [...reccuring.itemsMap.values()]
    },
    async openformDialog(id) {
      const [tempId, itemId] = id.split(':')
      const reccuring = _.findWhere(this.reccuring, {id: tempId})
      if (itemId) {
        const item = reccuring.itemsMap.get(id)
        this.formDialog.data = {
          ...item,
          reccuring: tempId
        }
      } else {
        this.formDialog.data.reccuring = tempId
      }
      this.formDialog.data.currency = reccuring.currency
      this.formDialog.show = true
    },
    async openUrlDialog(tempid) {
      this.urlDialog.data = _.findWhere(this.reccuring, {id: tempid})
      this.qrValue = this.urlDialog.data.lnurlpay

      // Connecting to our websocket fired in tasks.py
      this.connectWebocket(this.urlDialog.data.id)

      this.urlDialog.show = true
    },
    async closeformDialog() {
      this.formDialog.show = false
      this.formDialog.data = {}
    },
    async createInvoice(tempid) {
      ///////////////////////////////////////////////////
      ///Simple call to the api to create an invoice/////
      ///////////////////////////////////////////////////
      reccuring = _.findWhere(this.reccuring, {id: tempid})
      const wallet = _.findWhere(this.g.user.wallets, {id: reccuring.wallet})
      const data = {
        reccuring_id: tempid,
        amount: this.invoiceAmount,
        memo: 'Reccuring - ' + reccuring.name
      }
      await LNbits.api
        .request('POST', `/reccuring/api/v1/reccuring/payment`, wallet.inkey, data)
        .then(response => {
          this.qrValue = response.data.payment_request
          this.connectWebocket(wallet.inkey)
        })
        .catch(error => {
          LNbits.utils.notifyApiError(error)
        })
    },
    connectWebocket(reccuring_id) {
      //////////////////////////////////////////////////
      ///wait for pay action to happen and do a thing////
      ///////////////////////////////////////////////////
      if (location.protocol !== 'http:') {
        localUrl =
          'wss://' +
          document.domain +
          ':' +
          location.port +
          '/api/v1/ws/' +
          reccuring_id
      } else {
        localUrl =
          'ws://' +
          document.domain +
          ':' +
          location.port +
          '/api/v1/ws/' +
          reccuring_id
      }
      this.connection = new WebSocket(localUrl)
      this.connection.onmessage = () => {
        this.urlDialog.show = false
      }
    }
  },
  ///////////////////////////////////////////////////
  //////LIFECYCLE FUNCTIONS RUNNING ON PAGE LOAD/////
  ///////////////////////////////////////////////////
  async created() {
    await this.getReccurings()
  }
})
