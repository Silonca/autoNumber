# -*- coding: UTF-8 -*-
import argparse
import os
import sys

from typing import List

default_style = {
    'inherit': 'y',  # 是否继承父标题的编号，以及分隔父子标题编号的分隔符
    'heading': ['x', '*', '*', '*', '*', '*']
}

classic_style = {
    'inherit': 'n',
    'heading': ['x', '*、_cn', '(*)_cn', '*.', '(*)', '*)_en']
}


# 生成中文数字编号
def generate_cn(num):
    cn_num = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九']
    ten = num // 10
    one = num % 10
    if ten == 0:
        result = cn_num[one]
    elif one == 0:
        if ten == 1:
            result = '十'
        else:
            result = cn_num[ten] + '十'
    else:
        result = cn_num[ten] + '十' + cn_num[one]
    return result


# 生成大写中文数字编号
def generate_CN(num):
    cnu_num = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
    ten = num // 10
    one = num % 10
    if ten == 0:
        result = cnu_num[one]
    elif one == 0:
        if ten == 1:
            result = '拾'
        else:
            result = cnu_num[ten] + '拾'
    else:
        result = cnu_num[ten] + '拾' + cnu_num[one]
    return result


# 生成大写英文编号
def generate_EN(num):
    num -= 1
    ten = num // 26
    one = num % 26
    if ten == 0:
        result = chr(ord('A') + one)
    else:
        result = chr(ord('A') + ten - 1) + chr(ord('A') + one)
    return result


# 生成小写英文编号
def generate_en(num):
    num -= 1
    ten = num // 26
    one = num % 26
    if ten == 0:
        result = chr(ord('a') + one)
    else:
        result = chr(ord('a') + ten - 1) + chr(ord('a') + one)
    return result


# 生成罗马数字编号
def generate_roman(num):
    roman = [["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"],
             ["", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC"]]
    result = roman[1][int(num / 10 % 10)] + roman[0][num % 10]
    return result


# 生成十六进制编号
def generate_hex(num):
    return hex(num)


# 生成二级制编号
def generate_bin(num):
    return bin(num)


class AutoNumber:
    def __init__(self, style_name, files):
        if style_name.count(',') == 0:  # 未指定，本模块内查找
            assert hasattr(sys.modules[__name__], style_name), '未找到指定样式：' + style_name
            self.style = getattr(sys.modules[__name__], style_name)
        elif style_name.count(',') == 1:  # 指定了外部模块
            self.module_name, style_name = style_name.split(',')
            self.import_module = __import__(self.module_name)
            assert hasattr(self.import_module, style_name) or hasattr(sys.modules[__name__], style_name), \
                '未找到指定样式：' + self.import_module + ':' + style_name
            if hasattr(self.import_module, style_name):  # 外部定义的样式
                self.style = getattr(self.import_module, style_name)
            elif hasattr(sys.modules[__name__], style_name):  # 本模块定义的样式
                self.style = getattr(sys.modules[__name__], style_name)

        assert 'y' in self.style['inherit'] or self.style['inherit'] == 'n', '编号的继承关系设定错误'
        assert len(self.style['heading']) == 6, '标题的级数有误：' + str(len(self.style['heading']))
        self.inherit = True if 'y' in self.style['inherit'] else False
        if self.inherit:
            if ',' in self.style['inherit']:
                self.separator = self.style['inherit'].split(',', 1)[1]
            else:
                self.separator = '.'
        else:
            self.separator = ''
        if self.inherit:  # 可从二级标题开始编号
            for i in range(1, len(self.style['heading'])):
                assert self.style['heading'][i] != 'x', '继承关系下中间等级标题必须具有编号'
        self.toc: List[dict] = []
        self.files = files

    def generate_number(self, num, form) -> str:
        '''
        根据指定的编号形式生成编号

        :param num: 编号
        :param form: 编号形式
        :return: 生成的编号
        '''
        assert 1 <= num <= 99, '支持的编号范围：[1,99]'
        if self.import_module and hasattr(self.import_module, 'generate_' + form):  # 编号的方式定义在外部模块中
            return getattr(self.import_module, 'generate_' + form)(num)
        if hasattr(sys.modules[__name__], 'generate_' + form):  # 编号的方式定义在本模块中
            return getattr(sys.modules[__name__], 'generate_' + form)(num)
        assert False, '不支持的编号形式：' + form        # 两处均未找到，说明没有对该编号方式提供支持

    def pack_number(self, level, num):
        '''
        生成具有样式的编号

        :param level: 标题的等级
        :param num: 该等级的编号
        :return: 生成的具有样式的编号
        '''
        s = self.style['heading'][level - 1]
        if 'x' == s:  # 不编号
            return ''
        if '_' in s:  # 如果包含了'_'，就说明指定了某种数字外的编号方式
            s, lang = s.rsplit('_', 1)  # 以最后一个'_'为界分隔为两个部分
            num = self.generate_number(num, lang)
        prefix, suffix = s.split('*')  # 将*替换为对应的编号，其余字符保留作为样式
        return prefix + str(num) + suffix

    def parser_md(self, md_file):
        '''
        解析markdown文件

        :param md_file: markdown文件的文件名
        :return: 无
        '''
        with open(md_file, 'r', encoding='utf-8') as f:
            text = f.readlines()
            for i, l in enumerate(text):
                # 寻找标题行
                if l.startswith('#'):
                    heading, content = l.split(' ', 1)
                    level = heading.count('#')  # 获取标题级别
                    if len(self.toc) == 0:
                        assert level == 1, '起始标题应为一级标题，起始标题等级为：' + str(level)
                    elif len(self.toc) > 0:
                        assert level <= self.toc[-1]['level'] + 1, '标题等级跳跃，在第 ' + str(i) + ' 行：' + l
                    self.toc.append({'index': i, 'level': level, 'content': content, 'number': ''})

    def number(self):
        '''生成最近一个parse_md函数解析结果的编号'''
        for level in range(1, 7):
            cnt = 1
            prefix = ''
            for i, t in enumerate(self.toc):
                if t['level'] == level:
                    if i != 0 and self.toc[i - 1]['level'] < level:  # 等级提升，重新开始计数
                        cnt = 1
                    if cnt == 1 and level != 1:  # 新等级的第一条，根据上一条（即上一等级）确定前缀
                        if self.toc[i - 1]['number'] == '' or not self.inherit:  # 上一等级没有编号或非继承关系，前缀为空
                            prefix = ''
                        else:  # 正常前缀
                            prefix = self.toc[i - 1]['number'] + self.separator
                    t['number'] = prefix + self.pack_number(level, cnt)
                    cnt += 1

    def write_md(self, md_file):
        '''
        将编号写入指定文件

        :param md_file: 被写入的markdown文件的文件名
        :return: 无
        '''
        with open(md_file, 'r+', encoding='utf-8') as f:
            f.seek(0)
            text = f.readlines()
            for t in self.toc:
                if t['number'] == '':
                    text[t['index']] = '#' * t['level'] + ' ' + t['content']
                else:
                    text[t['index']] = '#' * t['level'] + ' ' + t['number'] + ' ' + t['content']
            f.seek(0)
            f.truncate(0)  # 清空文件
            f.seek(0)
            f.writelines(text)  # 写入编辑后的内容

    def run(self):
        '''开始批量生成/消除编号'''
        for filename in self.files:
            if not filename.endswith('.md'):
                filename += '.md'
            del self.toc
            self.toc = []
            self.parser_md(filename)
            print('parser:', filename)
            self.number()
            for i in self.toc:
                print(i['level'], i['number'])
            self.write_md(filename)  # 写入文件

    @classmethod
    def clear(cls, files):
        '''
        清除已有的编号

        :param files: 被清除编号的若干个文件的文件名
        :return: 无
        '''
        for filename in files:
            if not filename.endswith('.md'):
                filename += '.md'
            with open(filename, 'r+', encoding='utf-8') as f:
                f.seek(0)
                text = f.readlines()
                for i in range(len(text)):
                    if text[i].startswith('#'):
                        if text[i].count(' ') >= 2:  # 标题行至少有两个空格将该行分为三个部分，不考虑格式错误情况，将中间的编号部分清除
                            heading, _, content = text[i].split(' ', 2)
                            text[i] = heading + ' ' + content
                f.seek(0)
                f.truncate(0)  # 清空文件
                f.seek(0)
                f.writelines(text)  # 写入编辑后的内容


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--files', type=str, nargs='*', help='需要编号/消除编号的文件')
    parser.add_argument('-s', '--style', type=str, nargs='?',
                        help='编号的样式，指定为"clear"即消除已有编号，不指定即使用默认样式')
    parser.add_argument('--folders', nargs='*', help='包含需要编号/消除编号的文件的文件夹')
    args = parser.parse_args()

    assert (not args.files and args.folders) or (args.files and not args.folders), '必须指定待处理的文件或文件夹'
    if args.folders:  # 指定了文件夹，获取所有指定的文件夹中所有md文件
        files = []
        for folder in args.folders:
            folder_files = os.listdir(os.path.join(os.getcwd(), folder))  # 获取文件列表
            for f in folder_files:
                f = os.path.join(os.getcwd(), folder, f)  # 获得文件的绝对路径
                if f.endswith('.md'):
                    files.append(f)
    else:
        files = args.files

    if args.style:
        if args.style == 'clear':
            AutoNumber.clear(files)
            exit()
        style_name = args.style
    else:  # 未指定样式即使用默认样式
        style_name = 'default_style'
    an = AutoNumber(style_name, files)
    an.run()
