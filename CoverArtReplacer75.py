# -*- coding: UTF-8 -*-
import os
import io
import mimetypes
import wx
import eyed3
from PIL import Image, ImageFont, ImageDraw
import cv2
import numpy as np

class ImagePanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

    def display_image(self, input_image=''):
        if input_image == '' : image = 'input.gif' # デフォ画像
        else: image = input_image

        img = wx.Image(image) # 共通処理
        Newimg = img.Scale(300, 300, wx.IMAGE_QUALITY_HIGH)
        wx.StaticBitmap(self, -1, wx.Bitmap(Newimg))

        if input_image == '' :
            wx.StaticText(self, wx.ID_ANY, 'Audio File loaded.\nNo image detected.',(0,135), (300,30),style=wx.ALIGN_CENTER)

    def refresh_image_panel(self):
        image = 'input.gif'
        img = wx.Image(image)
        Newimg = img.Scale(300, 300, wx.IMAGE_QUALITY_HIGH) # 簡易スケール
        wx.StaticBitmap(self, -1, wx.Bitmap(Newimg))

class DirDropTarget(wx.FileDropTarget):
    def __init__(self, parent):
        super().__init__()
        self.textctrl = parent
    
    def OnDropFiles(self, x, y, filenames):
        if os.path.isdir(filenames[0]) == True:
            self.textctrl.SetValue(filenames[0])
        else :
            self.textctrl.SetValue(os.path.dirname(filenames[0]))
        return True

class ImageFileDropTarget(wx.FileDropTarget):
    def __init__(self, parent):
        super().__init__()
        self.panel = parent
        self.temp_path = []

    def get_image_path(self, dropped_path):
        self.ext = os.path.splitext(dropped_path[0])[1]
        return dropped_path

    def OnDropFiles(self, x, y, filenames):
        self.temp_path = self.get_image_path(filenames)
        self._panel()
        return True

    def _panel(self):
        if self.ext in ('.jpg','.png'): # 画像ファイル検出
            self.panel.display_image(self.temp_path[0])
            
        elif self.ext in ('.mp3', '.wav','.flac'): # オーディオファイル検出
            print('AudioFile in ImagePanel')

            self.song = eyed3.load(self.temp_path[0])
            if not self.song.tag : self.song.initTag() # タグが無いなら作る
            self.song_image = self.song.tag.images.get('') # 画像データの読み込み。['']だと存在、[]だとNone
            
            #画像表示
            if self.song_image != None: # 画像のあるオーディオ
                print('Image found. You can use this image data.')
                bytesio = io.BytesIO(self.song_image.image_data) # ioモジュールを使ってstream型へ
                self.panel.display_image(bytesio) # パネルへ渡す
            else: # 画像の無いオーディオ
                print('Images NOT found')
                self.panel.display_image('')
        else :
            print('非対応のファイル拡張子')
            return False

class AudioFileDropTarget(wx.FileDropTarget): 
    def __init__(self, parent):
        super().__init__()
        self.listctrl = parent
        self.temp_path = []

    def OnDropFiles(self, x, y, filenames):
        files = self.get_audio_path(filenames)
        self.__add_listctrl(files)
        return True

    def get_audio_path(self, dropped_path):
        temp_path = []
        for path in dropped_path:
            if os.path.isfile(path) == True:
                temp_path.append(path)
            if os.path.isdir(path) == True:
                for curDir, deep_dirs, files in os.walk(path):
                    for file in files:
                        temp_path.append(os.path.join(curDir, file))
        return temp_path

    def __add_listctrl(self, files):
        for i in files:
            flag = True
            if os.path.splitext(i)[1] not in ('.mp3'): flag = False # 非対応ファイルは読み込まない
            for dup in range(self.listctrl.GetItemCount()): # パス重複は読み込まない
                if i in self.listctrl.GetItemText(dup,2) : flag = False

            if flag == True: # 処理
                index = self.listctrl.InsertItem(self.listctrl.GetItemCount(), os.path.basename(i))

                audio_file = eyed3.load(i)
                if not audio_file.tag : audio_file.initTag()
                if audio_file.tag.images.get('') != None : 
                    self.listctrl.SetItem(index, 1, audio_file.tag.images.get('').mime_type)
                self.listctrl.SetItem(index, 2, i) # パス
        return True

    def listctrl_to_list(self):
        if self.listctrl.GetFirstSelected() == -1: # 選択無しの場合、全読み込み
            filelist = self._memorize_listctrl_all()
        else: # 選択あり
            filelist = self._memorize_listctrl_selected_path()
        return filelist

    def refresh_list_ctrl(self):
        mem_cnt = self.listctrl.GetSelectedItemCount()
        mem_select = self._memorize_listctrl_selected_index()

        temp = self._memorize_listctrl_all()

        self.listctrl.DeleteAllItems()
        self.__add_listctrl(temp)

        self._recall_select_index(mem_select, mem_cnt)
        return

    def _memorize_listctrl_all(self):
        filelist = [self.listctrl.GetItemText(len, 2) for len in range(self.listctrl.GetItemCount())] # 内包表記だと高速
        return filelist

    def _memorize_listctrl_selected_path(self):
        filelist = []
        index = self.listctrl.GetFirstSelected()
        for n in range(self.listctrl.GetSelectedItemCount()):
            filelist.append(self.listctrl.GetItemText(index,2))
            index = self.listctrl.GetNextSelected(index)
        return filelist

    def _memorize_listctrl_selected_index(self):
        memorize = []
        index = self.listctrl.GetFirstSelected()
        for n in range(self.listctrl.GetSelectedItemCount()):
            memorize.append(index)
            index = self.listctrl.GetNextSelected(index)
        return memorize

    def _recall_select_index(self, memorize, count):
        for n in range(count):
            self.listctrl.Select(memorize[n])
        return

    def select_all(self):
        for i in range(self.listctrl.GetItemCount()):
            self.listctrl.Select(i)

    def delete_selected_item(self):
        for n in range(self.listctrl.GetSelectedItemCount()):
            index = self.listctrl.GetNextSelected(-1)
            self.listctrl.DeleteItem(index)

    def copy_item(self):
        self.copy = self._memorize_listctrl_selected_path()
        return self.copy

    def cut_item(self):
        self.copy = self.copy_item()
        self.delete_selected_item()

    def paste_item(self):
        self.__add_listctrl(self.copy)
        return

class MyReplace(): # メイン機能
    def replace_audio_image(self, audio_file_list, cover_file_list): # 画像置き換え arg1:リスト,arg2:リスト

        already = 0
        for mlt_files in audio_file_list: # 確認用の読み込み
            audio_file = eyed3.load(mlt_files)
            if not audio_file.tag : audio_file.initTag() # タグが無いなら作る
            if audio_file.tag.images.get('') != None : already += 1 # 既カウント
        if already > 0 : 
            confirm = self.confirm_dialog('既に画像が埋め込まれたファイルが '+str(already)+'個あります。'\
            '（選択ファイル数：'+str(len(audio_file_list))+'）\n上書きしますか？')
            if confirm == 'cancel' : return False

        for mlt_files in audio_file_list: # メイン処理
            print('Target:' + mlt_files)
            audio_file = eyed3.load(mlt_files)
            if not audio_file.tag : audio_file.initTag() # タグが無いなら作る

            if self.dropB.ext in ('.jpg','.png') : # プレビューが画像ファイルの場合
                cover_mime = mimetypes.guess_type(cover_file_list[0])[0]
                with open(cover_file_list[0], 'rb') as cover_art :
                        audio_file.tag.images.set(3, cover_art.read(), cover_mime)

            else : # プレビューが画像ファイルじゃない場合、パネルを参照
                print('オーディオに埋め込まれた画像を利用します')
                cover_art = self.dropB.song_image.image_data
                cover_mime = self.dropB.song_image.mime_type
                audio_file.tag.images.set(3, cover_art, cover_mime)

            audio_file.tag.save(max_padding=64)

        print('-----Image Replaced-----')
        return audio_file_list

    def remove_audio_image(self, audio_file_list): # 画像を取り除く
        confirm = self.confirm_dialog(str(len(audio_file_list)) + '個のファイルが選択されました。\n埋め込まれた画像があれば削除します。')
        if confirm == 'cancel' : return False
        for mlt_files in audio_file_list:
            audio_file = eyed3.load(mlt_files)
            if not audio_file.tag : audio_file.initTag() # タグが無いなら作る
            audio_file.tag.images.remove('')
            audio_file.tag.save(max_padding=64)
        print('-----Image Removed-----')
        return audio_file_list

    def extract_audio_image(self, audio_file_list, set_dir): # 画像を抽出する

        overwrite = 0
        for filepath in audio_file_list:
            check_path = self._load_get_extract_path(filepath, set_dir)
            if check_path == False : continue # Falseをスキップ
            if os.path.exists(check_path) == True : overwrite += 1

        if overwrite > 0 : 
            confirm = self.confirm_dialog('抽出先に同名のファイルが存在しています。\n(対象数：'+str(overwrite)+')\n上書きしますか？')
            if confirm == 'cancel': return False

        for filepath in audio_file_list: # メイン処理
            target_path = self._load_get_extract_path(filepath, set_dir)
            if target_path == False : continue # Falseをスキップ

            for image in self.audio_file.tag.images: # 複数埋め込み/ファイル位置ブレ対応のfor
                with open(target_path, 'wb') as cover_art :
                    cover_art.write(image.image_data)

        print('-----Image Extracted-----')
        return False

    def check_dir_exist(self, dirpath):
        if os.path.exists(dirpath) == False:
            confirm = self.confirm_dialog('指定されたフォルダは存在しません。新しく作りますか？')
            if confirm == 'cancel' : return False
            os.makedirs(dirpath)

        return True
    
    def _load_get_extract_path(self, filepath, set_dir):
        self.audio_file = eyed3.load(filepath)
        if not self.audio_file.tag : self.audio_file.initTag() # タグが無いなら作る
        if self.audio_file.tag.images.get('') == None : return False # 抽出するイメージが含まれていないときFalse

        if set_dir == None:
            t_dir = os.path.dirname(filepath) # 保存先にオーディオファイルと同じディレクトリを指定
        else :
            t_dir = set_dir

        ext = mimetypes.guess_extension(self.audio_file.tag.images.get('').mime_type)
        album_name = self.audio_file.tag.album
        artist_name = self.audio_file.tag.artist

        filename = "{0} - {1}(image){2}".format(artist_name, album_name, ext)
        target = os.path.join(t_dir, filename)
        
        return target

class MyDialog(wx.MessageDialog):
    def confirm_dialog(self, dlg_message):
        dlg = wx.MessageDialog(None, dlg_message, '確認', style=wx.OK|wx.CANCEL)
        result = dlg.ShowModal()
        if result == wx.ID_OK : result = 'ok'
        elif result == wx.ID_CANCEL : result = 'cancel' # 閉じるボタンはキャンセル
        dlg.Destroy()
        return result

class MyFrame(wx.Frame, MyReplace, MyDialog): # GUI
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.CAPTION | wx.CLIP_CHILDREN | wx.CLOSE_BOX | wx.MINIMIZE_BOX | wx.SYSTEM_MENU
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((700, 510))
        self.SetTitle(u"[yf] CoverArtReplacer")
        
        self.panel_1 = ImagePanel(self) # ImagePanelから継承
        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(sizer_2, 1, wx.EXPAND, 0)

        sizer_3 = wx.StaticBoxSizer(wx.StaticBox(self.panel_1, wx.ID_ANY, u"対象のオーディオファイル"), wx.VERTICAL)
        sizer_2.Add(sizer_3, 1, wx.ALL | wx.EXPAND, 5)

        self.list_ctrl_1 = wx.ListCtrl(self.panel_1, wx.ID_ANY, style=wx.LC_HRULES | wx.LC_REPORT | wx.LC_VRULES)
        self.list_ctrl_1.SetMinSize((300, 300))
        self.list_ctrl_1.SetToolTip(u"ここにドラッグ&ドロップで読み込み")
        self.list_ctrl_1.AppendColumn("Name", format=wx.LIST_FORMAT_LEFT, width=200)
        self.list_ctrl_1.AppendColumn("Cover MIME", format=wx.LIST_FORMAT_LEFT, width=100)
        self.list_ctrl_1.AppendColumn("path", format=wx.LIST_FORMAT_LEFT, width=-1)
        sizer_3.Add(self.list_ctrl_1, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3.Add(sizer_4, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND | wx.SHAPED, 0)

        self.button_1 = wx.Button(self.panel_1, wx.ID_ANY, u"画像を削除")
        sizer_4.Add(self.button_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.button_2 = wx.Button(self.panel_1, wx.ID_ANY, u"画像を抽出")
        sizer_4.Add(self.button_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.button_5 = wx.Button(self.panel_1, wx.ID_ANY, u"リストをリセット")
        sizer_4.Add(self.button_5, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        sizer_5 = wx.StaticBoxSizer(wx.StaticBox(self.panel_1, wx.ID_ANY, u"埋め込む画像のプレビュー"), wx.VERTICAL)
        sizer_2.Add(sizer_5, 1, wx.ALL | wx.EXPAND, 5)

        self.panel_3 = ImagePanel(self.panel_1) # ImagePanelから継承
        self.panel_3.SetMinSize((300, 300))
        self.panel_3.SetToolTip(u"ここにドラッグ&ドロップで読み込み\n")
        sizer_5.Add(self.panel_3, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5.Add(sizer_6, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND | wx.SHAPED, 0)

        #self.text_ctrl_20 = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        #sizer_6.Add(self.text_ctrl_20, 2, wx.ALL, 5)
        self.button_15 = wx.Button(self.panel_1, wx.ID_ANY, u"選択から読み込む")
        sizer_6.Add(self.button_15, 0, wx.ALL, 5)

        self.button_4 = wx.Button(self.panel_1, wx.ID_ANY, u"パネルリセット")
        sizer_6.Add(self.button_4, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        sizer_7 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(sizer_7, 1, wx.EXPAND, 0)


        sizer_8 = wx.StaticBoxSizer(wx.StaticBox(self.panel_1, wx.ID_ANY, u"画像の抽出先"), wx.VERTICAL)
        sizer_7.Add(sizer_8, 1, wx.ALL | wx.EXPAND, 5)

        sizer_11 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_8.Add(sizer_11, 0, wx.EXPAND | wx.LEFT | wx.TOP, 5)

        self.radio_btn_curdir = wx.RadioButton(self.panel_1, wx.ID_ANY, u"オーディオと同じ位置")
        sizer_11.Add(self.radio_btn_curdir, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        sizer_10 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_8.Add(sizer_10, 0, wx.EXPAND | wx.LEFT | wx.TOP, 5)

        self.radio_btn_setdir = wx.RadioButton(self.panel_1, wx.ID_ANY, u"フォルダを指定")
        sizer_10.Add(self.radio_btn_setdir, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.text_ctrl_setdir = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        self.text_ctrl_setdir.SetMinSize((280, 23))
        
        sizer_10.Add(self.text_ctrl_setdir, 0, wx.ALL, 5)

        self.button_setdir = wx.Button(self.panel_1, wx.ID_ANY, u"参照", style=wx.BU_EXACTFIT)
        sizer_10.Add(self.button_setdir, 0, wx.ALL, 5)
        
        self.button_setdir_import = wx.Button(self.panel_1, wx.ID_ANY, u"選択から取得")
        sizer_10.Add(self.button_setdir_import, 0, wx.ALL, 5)

        sizer_7.Add((20, 100), 0, wx.ALL, 5)

        sizer_12 = wx.BoxSizer(wx.VERTICAL)
        sizer_7.Add(sizer_12, 1, wx.EXPAND, 0)

        self.button_3 = wx.Button(self.panel_1, wx.ID_ANY, u"埋込み実行")
        sizer_12.Add(self.button_3, 1, wx.ALL | wx.EXPAND, 5)

        self.button_10 = wx.Button(self.panel_1, wx.ID_ANY, u"リセット")
        sizer_12.Add(self.button_10, 1, wx.ALL | wx.EXPAND, 5)

        self.panel_1.SetSizer(sizer_1)

        self.Layout()
    # ここまでGUI設定(wx.Glade利用)

    # ラジオボタンinit
        self.radio_btn_curdir.SetValue(1)
        self.button_setdir.Enable(False)
        self.text_ctrl_setdir.Enable(False)
        self.button_setdir_import.Enable(False)

    # イベント
        self.Bind(wx.EVT_BUTTON, self.OnRemoveImage, self.button_1)
        self.Bind(wx.EVT_BUTTON, self.OnExtractImage, self.button_2)
        self.Bind(wx.EVT_BUTTON, self.OnExec, self.button_3)
        self.Bind(wx.EVT_BUTTON, self.OnResetImagePanel, self.button_4)
        self.Bind(wx.EVT_BUTTON, self.OnResetListCtrl, self.button_5)
        self.Bind(wx.EVT_BUTTON, self.OnResetAll, self.button_10)
        self.Bind(wx.EVT_BUTTON, self.OnImportAudioImage, self.button_15)
        self.Bind(wx.EVT_BUTTON, self.OnResetAll, self.button_10)
        self.radio_btn_curdir.Bind(wx.EVT_RADIOBUTTON, self.selected_radiobutton_curdir)
        self.radio_btn_setdir.Bind(wx.EVT_RADIOBUTTON, self.selected_radiobutton_setdir)
        self.Bind(wx.EVT_BUTTON, self.SetExtDirDialog, self.button_setdir)
        self.Bind(wx.EVT_BUTTON, self.SetExtDirImport, self.button_setdir_import)
        self.Bind(wx.EVT_LIST_KEY_DOWN, self.OnKey_ListCtrl)
        #self.Bind(wx.EVT_CHAR, self.OnHotKey_ListCtrl)
        
    # ドロップ機能のインスタンス生成
        self.dropA = AudioFileDropTarget(self.list_ctrl_1)
        self.dropA.listctrl.SetDropTarget(self.dropA)
        self.dropB = ImageFileDropTarget(self.panel_3)
        self.dropB.panel.SetDropTarget(self.dropB)
        self.dropC = DirDropTarget(self.text_ctrl_setdir)
        self.dropC.textctrl.SetDropTarget(self.dropC)

    #ExtPath
    def SetExtDirDialog(self, event):
        dialog = wx.DirDialog(None, u'抽出した画像を保存するフォルダを選択してください')
        dialog.ShowModal()
        dirpath = dialog.GetPath()
        self.text_ctrl_setdir.SetValue(dirpath)
    def SetExtDirImport(self, event):
        focus = self.dropA.listctrl.GetFocusedItem()
        if focus == -1 : return False
        filepath = self.dropA.listctrl.GetItemText(focus, 2)
        dirpath = os.path.dirname(filepath)
        self.text_ctrl_setdir.SetValue(dirpath)

    #ListCtrl
    def OnRemoveImage(self, event): # 画像を削除
        self.remove_audio_image(self.dropA.listctrl_to_list())
        self.dropA.refresh_list_ctrl()
        #self.dropA.reload_select()
    def OnExtractImage(self, event):  # 画像を抽出
        if self.radio_btn_curdir.GetValue() == True: # 同じ位置
            self.extract_audio_image(self.dropA.listctrl_to_list(), None)
        elif self.radio_btn_setdir.GetValue() == True: # フォルダ指定
            self.check_dir_exist(self.text_ctrl_setdir.GetValue())
            self.extract_audio_image(self.dropA.listctrl_to_list(), self.text_ctrl_setdir.GetValue())
        self.dropA.refresh_list_ctrl()

    def OnResetListCtrl(self, event):  # リストリセット
        self.dropA.listctrl.DeleteAllItems()
        self.dropA.temp_path = []

    #ImagePanel
    def OnResetImagePanel(self, event): # 画像リセット
        self.dropB.temp_path = []
        del self.dropB.song_image
        self.panel_3.refresh_image_panel()
    def OnImportAudioImage(self, event): ### リストから読み込む
        focus = self.dropA.listctrl.GetFocusedItem()
        if focus == -1 : return False
        self.dropB.OnDropFiles(0,0, [self.dropA.listctrl.GetItemText(focus, 2)])


    #Frame
    def OnExec(self, event): # 埋込み実行
        replace = self.replace_audio_image(self.dropA.listctrl_to_list(), self.dropB.temp_path)
        if replace == False : return False
        self.dropA.refresh_list_ctrl()

    def OnResetAll(self, event): # リセット
        self.OnResetImagePanel(event)
        self.OnResetListCtrl(event)


    # ラジオボタンによる挙動
    def selected_radiobutton_curdir(self, event):
        self.button_setdir.Enable(False)
        self.text_ctrl_setdir.Enable(False)
        self.button_setdir_import.Enable(False)
    def selected_radiobutton_setdir(self, event):
        self.button_setdir.Enable(True)
        self.text_ctrl_setdir.Enable(True)
        self.button_setdir_import.Enable(True)

    # キー入力イベント
    def OnKey_ListCtrl(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_DELETE: # アイテム削除 [DEL]
            self.dropA.delete_selected_item()
        if keycode ==  (wx.WXK_CONTROL and 65): # 全選択 [Ctrl+A] 65:Aキー
            self.dropA.select_all()
        if keycode ==  (wx.WXK_CONTROL and 88): # カット [Ctrl+X] 88:Xキー
            self.dropA.cut_item()
        if keycode ==  (wx.WXK_CONTROL and 67): # コピー [Ctrl+C] 67:Cキー
            self.dropA.copy_item()
        if keycode ==  (wx.WXK_CONTROL and 86): # ペースト [Ctrl+V] 86:Vキー
            self.dropA.paste_item()
        return

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True
        
if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
