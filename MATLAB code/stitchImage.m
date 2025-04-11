function imgFull = stitchImage(data,stepSize,xNum,yNum)
%% input
overlap = 1-stepSize*1e3/(2.2/50*45*1944);
imSz = size(data,1);
overlap_px = round(imSz*overlap);

for excitation = 1:2
    weight = [kron(linspace(0,1,overlap_px)',ones(1,imSz));ones(imSz-overlap_px*2,imSz);kron(linspace(1,0,overlap_px)',ones(1,imSz))].*...
        [kron(linspace(0,1,overlap_px),ones(imSz,1)),ones(imSz,imSz-overlap_px*2),kron(linspace(1,0,overlap_px),ones(imSz,1))];
    
    imgFullTmp = zeros((imSz-overlap_px)*(xNum-1)+imSz,(imSz-overlap_px)*(yNum-1)+imSz);
    for i = 1:xNum*yNum
        img = double(data(:,:,i,excitation));

        yPos = (xNum-1-floor((i-1)/yNum))*(imSz-overlap_px);
        if rem(floor((i-1)/yNum),2)
            xPos = (i-floor((i-1)/yNum)*yNum-1)*(imSz-overlap_px);
        else
            xPos = (yNum-(i-floor((i-1)/yNum)*yNum))*(imSz-overlap_px);
        end
        imgFullTmp(yPos+(1:imSz),xPos+(1:imSz)) = imgFullTmp(yPos+(1:imSz),xPos+(1:imSz)) + ...
            img.*weight*255;
    end

    imgFullTmp = imgFullTmp(overlap_px:end-overlap_px,overlap_px:end-overlap_px);
    
    imgFull(:,:,excitation) = uint16(round(imgFullTmp));
end

end