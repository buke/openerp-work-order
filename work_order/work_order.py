# -*- coding: utf-8 -*-
##############################################################################
#
#    Work Order
#    Copyright 2013 wangbuke <wangbuke@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp import netsvc

class work_order(osv.osv):

    def _get_default_shop(self, cr, uid, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        shop_ids = self.pool.get('sale.shop').search(cr, uid, [('company_id','=',company_id)], context=context)
        if not shop_ids:
            raise osv.except_osv(_('Error!'), _('There is no default shop for the current user\'s company!'))
        return shop_ids[0]

    _name = "work.order"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Work Order"

    _columns = {
        'name': fields.char('Order Reference', size=64, required=True, select=True),
        'sale_order_id': fields.many2one('sale.order', 'Order', required=True, domain=[('state', 'not in', ['done', 'cancel'])]),
        'shop_id': fields.many2one('sale.shop', 'Shop', required=True),
        'origin': fields.char('Source Document', size=64, help="Reference of the document that generated this sales order request."),
        'client_order_ref': fields.char('Customer Reference', size=64),
        'state': fields.selection([
            ('draft', 'Draft Order'), # 新建
            ('waiting_accepted', 'Waiting Accepted'), # 等待接单
            ('rejected', 'Order Rejected'), # 被拒绝
            ('blocked', 'Order Blocked'), # 超时
            ('manual', 'Need customer service'), # 人工调度
            ('accepted', 'Accepted'), # 已接单
            ('started', 'Started'), # 开始
            ('ended', 'Ended'), # 结束
            ('done', 'Done'),
            ('cancel', 'Cancelled'), # 取消
            ], 'Status', readonly=True, track_visibility='onchange',
            help="", select=True),
        'date_order': fields.date('Date', required=True, select=True),
        'confirm_date': fields.datetime('Confirm Date', readonly=True, select=True, help="Date on which order is confirmed."),
    }

    _defaults = {
        'state': 'draft',
        'date_order': fields.date.context_today,
        'name': lambda obj, cr, uid, context: '/',
        'shop_id': _get_default_shop,
    }

    def check_invoice(self, cr, uid, ids, *args):
        '''
        检查发票金额. 如果不一致，则修改原订单。
        如：租车超出时间，额外加钱则需新建一条 sale.order.line .
        '''
        return True

    def act_waiting_accept(self, cr, uid, ids, context=None):
        '''
        工单确认，进入待分配状态
        '''
        self.write(cr, uid, ids, {'state':'waiting_accepted', 'confirm_date':fields.date.context_today(self, cr, uid, context=context)}, context=context)
        #TODO 通知司机派单
        return True

    def act_reject(self, cr, uid, ids, context=None):
        '''
        工单被所有商家拒绝
        '''
        self.write(cr, uid, ids, {'state':'rejected'}, context=context)
        return True

    def act_block(self, cr, uid, ids, context=None):
        '''
        工单超时，系统拒绝
        '''
        self.write(cr, uid, ids, {'state':'blocked'}, context=context)
        return True

    def act_cancel(self, cr, uid, ids, context=None):
        '''
        工单取消
        '''
        self.write(cr, uid, ids, {'state':'cancel'}, context=context)
        return True

    def act_accept(self, cr, uid, ids, context=None):
        '''
        工单被接受
        '''
        self.write(cr, uid, ids, {'state':'accepted'}, context=context)
        return True

    def act_start(self, cr, uid, ids, context=None):
        '''
        工单经过双重确认(sig_business_start & sig_customer_start)开始
        '''
        self.write(cr, uid, ids, {'state':'started'}, context=context)
        return True

    def act_manual(self, cr, uid, ids, context=None):
        '''
        人工调度工单
        '''
        self.write(cr, uid, ids, {'state':'manual'}, context=context)
        return True

    def act_end(self, cr, uid, ids, context=None):
        '''
        工单经过双重确认结束(sig_business_end & sig_customer_end)
        '''
        self.write(cr, uid, ids, {'state':'ended'}, context=context)
        return True

    def act_sale_order(self, cr, uid, ids, context=None):
        '''
        返回工单所对应的销售订单，并进入销售订单子工作流
        '''
        work_order = self.browse(cr, uid, ids[0], context=context)
        return work_order.sale_order_id.id

    def act_sale_order_except(self, cr, uid, ids, context=None):
        '''
        销售订单子工作流异常
        '''
        return True

    def act_sale_order_done(self, cr, uid, ids, context=None):
        '''
        销售订单子工作流完成
        '''
        return True

    def act_done(self, cr, uid, ids, context=None):
        '''
        工单完成
        '''
        self.write(cr, uid, ids, {'state':'done'}, context=context)
        return True

    def act_wait_business_start(self, cr, uid, ids, context=None):
        '''
        等待商家确认开始
        '''
        return True

    def act_wait_customer_start(self, cr, uid, ids, context=None):
        '''
        等待用户确认开始
        '''
        return True

    def _check_block_order(self, cr, uid, ids=False, context=None):
        '''
        定时任务：检查3分钟内是否有人接单
        '''
        #TODO check confirm_date
        #1. search 符合条件 work order
        #2. 对超时订单 trg_validate sig_block
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
