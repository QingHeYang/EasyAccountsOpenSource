package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.dto.TypeSingleDto;
import com.deepblue.yd_jz.entity.Type;
import com.deepblue.yd_jz.dto.TypeListResponseDto;
import com.deepblue.yd_jz.service.TypeService;
import com.deepblue.yd_jz.dto.BaseDto;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/type")
@Api(value = "TypeController", tags = {"分类管理"})
public class TypeController {
    @Autowired
    TypeService typeService;

    @ApiOperation(value = "添加分类", notes = "添加分类")
    @PostMapping("/addType")
    public BaseDto addType(@RequestBody TypeSingleDto type) {
        if (type.getParent()==null){
            type.setParent(-1);
        }
        typeService.addType(type);
        return BaseDto.setSuccessBean();
    }

    @ApiOperation(value = "更新分类", notes = "更新分类")
    @PutMapping("/updateType/{id}")
    public BaseDto updateType(@PathVariable int id, @RequestBody TypeSingleDto type){
        typeService.updateType(type);
        return BaseDto.setSuccessBean();
    }

    @ApiOperation(value = "停用分类", notes = "停用分类")
    @DeleteMapping("/deleteType/{id}")
    public BaseDto deleteType(@PathVariable int id){
        typeService.disableType(id);
        return BaseDto.setSuccessBean();
    }

    @ApiOperation(value = "归档分类", notes = "归档分类")
    @PutMapping("/archiveType/{id}")
    public BaseDto archiveType(@PathVariable int id, @RequestParam boolean archive){
        typeService.archiveType(id, archive);
        return BaseDto.setSuccessBean();
    }

    @ApiOperation(value = "获取二级指定分类", notes = "获取二级指定分类")
    @GetMapping("/getType/{parent}")
    public BaseDto<List<Type>> getType(@PathVariable int parent){
        BaseDto<List<Type>> baseDto = BaseDto.setSuccessBean();
        baseDto.setData(typeService.queryTypeList(parent));
        return baseDto;
    }

    @ApiOperation(value = "获取所有分类", notes = "获取所有分类")
    @GetMapping("/getType")
    public BaseDto<List<TypeListResponseDto>> getType(){
        List<TypeListResponseDto> toClients = typeService.queryAllType(true);
        BaseDto<List<TypeListResponseDto>> baseDto = BaseDto.setSuccessBean();
        baseDto.setData(toClients);
        return baseDto;
    }

    @ApiOperation(value = "获取指定收支的分类", notes = "获取指定收支的分类")
    @GetMapping("/getTypeByActionId/{actionId}")
    public BaseDto<List<TypeListResponseDto>> getTypeByActionId(@PathVariable int actionId){
        List<TypeListResponseDto> toClients = typeService.queryTypeByActionId(actionId);
        BaseDto<List<TypeListResponseDto>> baseDto = BaseDto.setSuccessBean();
        baseDto.setData(toClients);
        return baseDto;
    }

    @ApiOperation(value = "获取所有分类（无归档、停用限制）", notes = "获取所有分类（无归档、停用限制）")
    @GetMapping("/getType/noLimit")
    public BaseDto<List<TypeListResponseDto>> getTypeNoLimit(){
        List<TypeListResponseDto> toClients = typeService.queryAllType(false);
        BaseDto<List<TypeListResponseDto>> baseDto = BaseDto.setSuccessBean();
        baseDto.setData(toClients);
        return baseDto;
    }

    @ApiOperation(value = "获取单个分类", notes = "获取单个分类")
    @GetMapping("/getTypeSingle/{id}")
    public BaseDto<Type> getTypeSingle(@PathVariable int id){
        BaseDto<Type> baseDto = BaseDto.setSuccessBean();
        baseDto.setData(typeService.queryTypeSingle(id));
        return baseDto;
    }

    @ApiOperation(value = "获取归档分类", notes = "获取归档分类")
    @GetMapping("/getTypeArchive")
    public BaseDto<List<TypeListResponseDto>> getTypeArchive(){
        List<TypeListResponseDto> toClients = typeService.queryTypeArchive();
        BaseDto<List<TypeListResponseDto>> baseDto = BaseDto.setSuccessBean();
        baseDto.setData(toClients);
        return baseDto;
    }

}
