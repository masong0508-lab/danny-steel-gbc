import cv2, numpy as np, sys
S=0.25
a=cv2.imread('/mnt/user-data/uploads/20260929_152116.jpg'); b=cv2.imread('/mnt/user-data/uploads/20260929_152136.jpg')
A=cv2.resize(a,None,fx=S,fy=S,interpolation=cv2.INTER_AREA).astype(np.float32)
B=cv2.resize(b,None,fx=S,fy=S,interpolation=cv2.INTER_AREA).astype(np.float32)
s,tx,ty,rot=[float(v) for v in sys.argv[1:5]]
W=int(tx+B.shape[1]*s)+10; H=int(max(A.shape[0],ty+B.shape[0]*s))+10
c,sn=np.cos(np.radians(rot)),np.sin(np.radians(rot))
M=np.array([[s*c,-s*sn,tx],[s*sn,s*c,ty]],np.float32)
wb=cv2.warpAffine(B,M,(W,H),flags=cv2.INTER_LINEAR)
mb=cv2.warpAffine(np.ones(B.shape[:2],np.float32),M,(W,H),flags=cv2.INTER_LINEAR)
ca=np.zeros((H,W,3),np.float32); ca[:A.shape[0],:A.shape[1]]=A
ma=np.zeros((H,W),np.float32); ma[:A.shape[0],:A.shape[1]]=1
ov=(ma>0.99)&(mb>0.99)
print('overlap px',ov.sum(), 'canvas',W,H)
# colour-match B to A in overlap (per channel gain/offset)
wb2=wb.copy()
if ov.sum()>500:
    for k in range(3):
        x=wb[...,k][ov]; y=ca[...,k][ov]
        g=y.std()/(x.std()+1e-6); o=y.mean()-g*x.mean(); wb2[...,k]=wb[...,k]*g+o
# feather blend across overlap columns
cols=np.where(ov.any(0))[0]
x0,x1=cols.min(),cols.max()
ramp=np.clip((np.arange(W)-x0)/max(1,x1-x0),0,1)[None,:]
wa_=ma*(1-ramp*(mb>0)); wb_=mb*np.where(ma>0,ramp,1)
out=(ca*wa_[...,None]+wb2*wb_[...,None])/np.maximum(wa_+wb_,1e-6)[...,None]
valid=((ma>0)|(mb>0.99))
out=np.clip(out,0,255).astype(np.uint8)
cv2.imwrite('pano_raw.png',out)
# crop to rows fully covered by both (common vertical range)
rows=np.where((ma[:,x0-5]>0.99)&(mb[:,x1+5 if x1+5<W else W-1]>0.99))[0]
print('rows',rows.min(),rows.max(),'ov x',x0,x1)
prev=cv2.resize(out,None,fx=0.9,fy=0.9)
cv2.imwrite('pano_prev.jpg',prev)
