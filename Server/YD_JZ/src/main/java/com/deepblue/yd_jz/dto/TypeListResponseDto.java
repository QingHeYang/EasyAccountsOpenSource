package com.deepblue.yd_jz.dto;

import com.deepblue.yd_jz.entity.Action;
import com.deepblue.yd_jz.entity.Type;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;

import java.util.List;

@Slf4j
@Data
public class TypeListResponseDto {
    private int id;
    private String tName;
    private Integer parent;
    private List<TypeListResponseDto> childrenTypes;

    private boolean disable = false;  // Default is false

    private boolean hasChild = false;  // Default is false

    private Boolean archive;  // Nullable Boolean field

    private Action action;  // Entity relationship

    public TypeListResponseDto convertToDto(Type type) {
        if (type == null) {
            return this;
        }
        TypeListResponseDto typeListResponseDto = this;
        typeListResponseDto.setId(type.getId());
        String noticeStr = "";
        if (type.getArchive()!=null&&type.getArchive()){
            noticeStr = "(已归档)";
        }
        if (type.isDisable()){
            noticeStr = "(已停用)";
        }
        typeListResponseDto.setTName(type.getTName()+noticeStr);
        typeListResponseDto.setParent(type.getParent());
        typeListResponseDto.setDisable(type.isDisable());
        typeListResponseDto.setHasChild(type.isHasChild());
        typeListResponseDto.setArchive(type.getArchive());
        typeListResponseDto.setAction(type.getAction());
        return typeListResponseDto;
    }
}
