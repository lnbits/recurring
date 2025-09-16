window.app = Vue.createApp({
  el: '#vue',
  mixins: [windowMixin],
  delimiters: ['${', '}'],
  data: function () {
    return {
      recurring: [],
      recurringTable: {
        columns: [
          {name: 'live', align: 'left', label: 'live', field: 'check_live'},
          {name: 'id', align: 'left', label: 'id', field: 'id'},
          {
            name: 'price_id',
            align: 'left',
            label: 'price_id',
            field: 'price_id'
          },
          {
            name: 'wallet_id',
            align: 'left',
            label: 'wallet_id',
            field: 'wallet_id'
          },
          {
            name: 'customer_email',
            align: 'left',
            label: 'customer_email',
            field: 'customer_email'
          }
        ],
        pagination: {
          rowsPerPage: 10
        }
      }
    }
  },
  methods: {
    async getReccurings() {
      await LNbits.api
        .request('GET', '/recurring/api/v1', this.g.user.wallets[0].adminkey)
        .then(response => {
          this.recurring = response.data
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
    async createReccuring(wallet, data) {
      data.wallet = wallet.id
      await LNbits.api
        .request('POST', '/recurring/api/v1', wallet.adminkey, data)
        .then(response => {
          this.recurring.push(response.data)
          this.closeFormDialog()
        })
        .catch(error => {
          LNbits.utils.notifyApiError(error)
        })
    },
    async exportCSV() {
      await LNbits.utils.exportCSV(this.recurringTable.columns, this.recurring)
    }
  },
  async created() {
    await this.getReccurings()
  }
})
