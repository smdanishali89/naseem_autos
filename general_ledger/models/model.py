# -*- coding: utf-8 -*-
from openerp import models, fields, api
from datetime import timedelta,datetime,date
from odoo.exceptions import Warning, ValidationError



class general_ledger(models.Model):
	_name = "general.ledger"
	_rec_name = "date"


	date = fields.Date(string="Date", default = date.today())
	journal = fields.Many2one('account.journal', string="Journal", required="1")
	move_id = fields.Many2one('account.move', string="Entry")
	bridge_acc = fields.Many2one('account.account', string="Bridge Account")
	ledger_tree = fields.One2many('general.ledger.tree', 'tree_link')

	stages = fields.Selection([
		('draft', 'Draft'),
		('validate', 'Validate'),
		],default='draft')




	# =================== Button Actions Portion START =========================
	@api.multi
	def validate(self):
		print ("Validate Pressed")
		self.create_journal_entry_form()
		self.create_entry_lines()
		self.stages = 'validate'



	@api.multi
	def set_to_draft(self):
		print ("Draft Pressed")
		# Deleting Move ID Tree lines
		if self.move_id:
			self.move_id.button_cancel()
		if self.move_id.line_ids:
			self.move_id.line_ids.unlink()
		self.stages = 'draft'


	# =================== Button Actions Portion ENDS ==========================


	def create_journal_entry_form(self):
		journal_entries = self.env['account.move']
		journal_entries_lines = self.env['account.move.line']

		if not self.move_id:   
			create_journal_entry = journal_entries.create({
					'journal_id': self.journal.id,
					'date':self.date,
					'ref' : "Journal Legder Entry",
					})

			self.move_id = create_journal_entry.id
		else:
			self.move_id.journal_id = self.journal.id
			self.move_id.date = self.date


	def create_entry_lines(self):

		comp_rec = self.env['res.company'].search([], limit=1)
		temp_bridge_acc = comp_rec[0].inter_ou_clearing_account_id.id


		entry_lines = []
		for x in self.ledger_tree:


			currency_multiply = 1
			base_currency_rec = None
			if x.currency:
				base_currency_rec = self.env['res.company'].search([('currency_id','=',x.currency.id)])
				if base_currency_rec:
					currency_multiply = x.currency.rate

			# if x.tax:
			# 	credit = x.amount
			# else:
			# 	credit = x.net_amount

			# Scenrario where only main OU is given
			if x.main_ou and not x.expense_ou:
				if x.vat_nature == 'debit':
					debit = x.net_amount
					credit = x.amount
				else:
					debit = x.amount
					credit = x.net_amount

				# Debit Entry
				temp_currency = None
				temp_currency_amount = 0
				if not base_currency_rec:
					temp_currency = x.currency.id
					temp_currency_amount = debit
				entry_lines.append({
					'account_id':x.debit_acc.id,
					'partner_id':x.partner_id.id,
					'name':x.description,
					# 'debit':x.net_amount,
					'debit':debit * currency_multiply,
					'operating_unit_id':x.oca.id,
					'amount_currency':temp_currency_amount,
					'currency_id':temp_currency,
					'analytic_account_id':x.analytic_acc.id,
					'analytic_tag_ids':x.analytic_tag.id,
					'move_id':self.move_id.id,
					})

				# Credit Entry
				temp_currency = None
				temp_currency_amount = 0
				if not base_currency_rec:
					temp_currency = x.currency.id
					temp_currency_amount = credit
				entry_lines.append({
					'account_id':x.credit_acc.id,
					'partner_id':x.partner_id.id,
					'name':x.description,
					'credit':credit * currency_multiply,
					'amount_currency':-1*(temp_currency_amount),
					'currency_id':temp_currency,
					# 'credit':x.amount,
					'operating_unit_id':x.oca.id,
					'analytic_account_id':x.analytic_acc.id,
					'analytic_tag_ids':x.analytic_tag.id,
					'move_id':self.move_id.id,
					})


				# Tax Entry
				if x.tax:

					if x.vat_nature == 'debit':
						temp_currency = None
						temp_currency_amount = 0
						if not base_currency_rec:
							temp_currency = x.currency.id
							temp_currency_amount = x.tax_amount

						entry_lines.append({
							'account_id':x.tax.account_id.id,
							'partner_id':x.partner_id.id,
							'name':x.description + " Tax Debited",
							'debit':x.tax_amount * currency_multiply,
							'operating_unit_id':x.oca.id,
							'amount_currency':temp_currency_amount,
							'currency_id':temp_currency,
							'analytic_account_id':x.analytic_acc.id,
							'analytic_tag_ids':x.analytic_tag.id,
							'move_id':self.move_id.id,
							})
					# if vat_nature == 'credit':
					else:
						temp_currency = None
						temp_currency_amount = 0
						if not base_currency_rec:
							temp_currency = x.currency.id
							temp_currency_amount = x.tax_amount
						entry_lines.append({
							'account_id':x.tax.account_id.id,
							'partner_id':x.partner_id.id,
							'name':x.description + " Tax Credited",
							'credit':x.tax_amount * currency_multiply,
							'operating_unit_id':x.oca.id,
							'amount_currency':-1*(temp_currency_amount),
							'currency_id':temp_currency,
							'analytic_account_id':x.analytic_acc.id,
							'analytic_tag_ids':x.analytic_tag.id,
							'move_id':self.move_id.id,
							})


			if x.main_ou and x.expense_ou:
				if x.vat_nature == 'debit':
					main_debit = x.amount
					main_credit = x.amount
					exp_debit = x.net_amount
					exp_credit = x.amount
				else:
					exp_debit = x.amount
					exp_credit = x.amount
					main_debit = x.amount
					main_credit = x.net_amount


				# Debit Entry in Main OU
				print ("1111111111111111111111111")
				temp_currency = None
				temp_currency_amount = 0
				if not base_currency_rec:
					temp_currency = x.currency.id
					temp_currency_amount = main_debit
				entry_lines.append({
					# 'account_id':x.debit_acc.id,
					'account_id':temp_bridge_acc,
					'partner_id':x.partner_id.id,
					'name':x.description,
					'amount_currency':temp_currency_amount,
					'currency_id':temp_currency,
					# 'debit':x.net_amount,
					'debit':main_debit * currency_multiply,
					'operating_unit_id':x.main_ou.id,
					'analytic_account_id':x.analytic_acc.id,
					'analytic_tag_ids':x.analytic_tag.id,
					'move_id':self.move_id.id,
					})

				print ("222222222222222222222")
				# Credit Entry in Main OU
				temp_currency = None
				temp_currency_amount = 0
				if not base_currency_rec:
					temp_currency = x.currency.id
					temp_currency_amount = main_credit
				entry_lines.append({
					'account_id':x.credit_acc.id,
					'partner_id':x.partner_id.id,
					'name':x.description,
					'amount_currency':-1*(temp_currency_amount),
					'currency_id':temp_currency,
					'credit':main_credit * currency_multiply,
					# 'credit':x.amount,
					'operating_unit_id':x.main_ou.id,
					'analytic_account_id':x.analytic_acc.id,
					'analytic_tag_ids':x.analytic_tag.id,
					'move_id':self.move_id.id,
					})

				print ("444444444444444444444444444")
				# Debit Entry in Expense OU
				temp_currency = None
				temp_currency_amount = 0
				if not base_currency_rec:
					temp_currency = x.currency.id
					temp_currency_amount = exp_debit
				entry_lines.append({
					'account_id':x.debit_acc.id,
					'partner_id':x.partner_id.id,
					'name':x.description,
					'amount_currency':temp_currency_amount,
					'currency_id':temp_currency,
					# 'debit':x.net_amount,
					'debit':exp_debit * currency_multiply,
					'operating_unit_id':x.expense_ou.id,
					'analytic_account_id':x.analytic_acc.id,
					'analytic_tag_ids':x.analytic_tag.id,
					'move_id':self.move_id.id,
					})

				print ("55555555555555555555")
				# Credit Entry in Expense OU
				temp_currency = None
				temp_currency_amount = 0
				if not base_currency_rec:
					temp_currency = x.currency.id
					temp_currency_amount = exp_credit
				entry_lines.append({
					# 'account_id':x.credit_acc.id,
					'account_id':temp_bridge_acc,
					'partner_id':x.partner_id.id,
					'name':x.description,
					'amount_currency':-1*(temp_currency_amount),
					'currency_id':temp_currency,
					'credit':exp_credit * currency_multiply,
					# 'credit':x.amount,
					'operating_unit_id':x.expense_ou.id,
					'analytic_account_id':x.analytic_acc.id,
					'analytic_tag_ids':x.analytic_tag.id,
					'move_id':self.move_id.id,
					})


				# Tax Entry
				if x.tax:

					# if x.vat_nature == 'debit':
					if x.vat_nature == 'credit':
						temp_currency = None
						temp_currency_amount = 0
						if not base_currency_rec:
							temp_currency = x.currency.id
							temp_currency_amount = x.tax_amount
						print ("66666666666666666666666666")
						entry_lines.append({
							'account_id':x.tax.account_id.id,
							'partner_id':x.partner_id.id,
							'name':x.description + " Tax Debited",
							# 'debit':x.tax_amount,
							'credit':x.tax_amount * currency_multiply,
							'amount_currency':-1*(temp_currency_amount),
							'currency_id':temp_currency,
							'operating_unit_id':x.main_ou.id,
							'analytic_account_id':x.analytic_acc.id,
							'analytic_tag_ids':x.analytic_tag.id,
							'move_id':self.move_id.id,
							})
					# if vat_nature == 'credit':
					# else:
					# 	print ("77777777777777777777777777")
					# 	entry_lines.append({
					# 		'account_id':x.tax.account_id.id,
					# 		'partner_id':x.partner_id.id,
					# 		'name':x.description + " Tax Credited",
					# 		'credit':x.tax_amount,
					# 		'oca':x.main_ou.id,
					# 		'analytic_acc':x.analytic_acc.id,
					# 		'analytic_tag':x.analytic_tag.id,
					# 		'move_id':self.move_id.id,
					# 		})


					if x.vat_nature == 'debit':
						temp_currency = None
						temp_currency_amount = 0
						if not base_currency_rec:
							temp_currency = x.currency.id
							temp_currency_amount = x.tax_amount
						print ("8888888888888888888888")
						entry_lines.append({
							'account_id':x.tax.account_id.id,
							'partner_id':x.partner_id.id,
							'name':x.description + " Tax Debited",
							'debit':x.tax_amount * currency_multiply,
							'operating_unit_id':x.expense_ou.id,
							'amount_currency':temp_currency_amount,
							'currency_id':temp_currency,
							'analytic_account_id':x.analytic_acc.id,
							'analytic_tag_ids':x.analytic_tag.id,
							'move_id':self.move_id.id,
							})
					# if vat_nature == 'credit':
					# else:
					# 	print ("99999999999999999999999999999")
					# 	entry_lines.append({
					# 		'account_id':x.tax.account_id.id,
					# 		'partner_id':x.partner_id.id,
					# 		'name':x.description + " Tax Credited",
					# 		'credit':x.tax_amount,
					# 		'oca':x.expense_ou.id,
					# 		'analytic_acc':x.analytic_acc.id,
					# 		'analytic_tag':x.analytic_tag.id,
					# 		'move_id':self.move_id.id,
					# 		})

					# 	print ("0000000000000000000000000000000")

		self.move_id.line_ids = entry_lines
		self.move_id.post()



	# Overriding Unlink funtion to avoid unlinking the entry in validated stage
	@api.multi
	def unlink(self):
		if self.stages == 'validate':
			raise ValidationError("Can't delete a validated entry.")
		rec = super(general_ledger, self).unlink()

		return rec

# =================== Internal Tree Class Portion START =========================
class general_ledger_tree(models.Model):
	_name = "general.ledger.tree"

	
	description = fields.Char(string="Description", required="1")
	debit_acc = fields.Many2one('account.account', string="Debit Account", required="1")
	credit_acc = fields.Many2one('account.account', string="Credit Account", required="1")
	amount = fields.Float(string="Amount")
	main_ou = fields.Many2one('operating.unit', string="Main OU")
	expense_ou = fields.Many2one('operating.unit', string="Expense OU")


	currency = fields.Many2one('res.currency', string="Currency")
	analytic_acc = fields.Many2one('account.analytic.account', string="Analytic Account")
	analytic_tag = fields.Many2one('account.analytic.tag', string="Analytic Tag")
	invoice_no = fields.Char(string="Invoice No")
	ref_no = fields.Char(string="Reference No")
	invoice_date = fields.Date(string="Invoice Date")


	tax = fields.Many2one('account.tax', string="VAT")
	tax_amount = fields.Float(string="VAT Amount")
	net_amount = fields.Float(string="Net Amount")
	partner_id = fields.Many2one('res.partner', string='Partner')

	trans_type = fields.Selection([
		('inclusive', 'Inclusive'),
		('exclusive', 'Exclusive'),
		], default="inclusive", string="Type")

	vat_nature = fields.Selection([
		('debit', 'Debit'),
		('credit', 'Credit'),
		], string="VAT Nature", required=True)

	tree_link = fields.Many2one('general_ledger')




	@api.onchange('tax', 'amount', 'trans_type','vat_nature')
	def tax_amount_change(self):
		print ("CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCc")
		if self.trans_type == 'inclusive':
			self.tax_amount = (self.amount * self.tax.amount)/(100 + self.tax.amount)
			print ("inclusive")
		else:
			print ("exclusive")
			self.tax_amount = self.tax.amount/100 * self.amount


	@api.onchange('amount', 'tax_amount')
	def net_amount_change(self):
		self.net_amount = self.amount - self.tax_amount


# =================== Internal Tree Class Portion ENDS ==========================



# =============== Account Move Class Inherit Portion START =====================
class account_move_extend(models.Model):
	_inherit = 'account.move'




	# Overriding below function to allow enter unbalanced journal entries
	@api.multi
	def assert_balanced(self):
		if not self.ids:
			return True
		prec = self.env['decimal.precision'].precision_get('Account')

		self._cr.execute("""\
			SELECT      move_id
			FROM        account_move_line
			WHERE       move_id in %s
			GROUP BY    move_id
			HAVING      abs(sum(debit) - sum(credit)) > %s
			""", (tuple(self.ids), 10 ** (-max(5, prec))))
		# if len(self._cr.fetchall()) != 0:
		#     raise UserError(_("Cannot create unbalanced journal entry."))
		return True
# =============== Account Move Class Inherit Portion ENDS ======================




# =============== Account Move Line Class Inherit Portion START =====================
class account_move_line_extend(models.Model):
	_inherit = 'account.move.line'


	oca = fields.Many2one('operating.unit', string="OCA")
	analytic_acc = fields.Many2one('account.analytic.account', string="Analytic Account")
	analytic_tag = fields.Many2one('account.analytic.tag', string="Analytic Tag")


# =============== Account Move Line Class Inherit Portion ENDS ======================